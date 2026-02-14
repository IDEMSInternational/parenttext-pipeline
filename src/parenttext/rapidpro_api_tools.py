"""
# rapidpro_api_tools.py
This script acts as a CLI for various RapidPro API operations.
Currently supported operations:
    - count_flow_runs: Calculates run statistics for specific flows defined in .env
    - process_deletion_requests: Deletes messages, runs, and contacts for users in a specific group.
    - export_contacts: Exports contact data to CSV with whitelisted fields and group memberships.

Usage:
    python -m parenttext.rapidpro_api_tools --steps count_flow_runs
    python -m parenttext.rapidpro_api_tools --steps process_deletion_requests --dry-run
    python -m parenttext.rapidpro_api_tools --steps export_contacts
"""

import argparse
import csv
import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from os import getenv
import json

env = {}


def safe_getenv(key, default):
    if key not in env.keys():
        env[key] = getenv(key)

    if env[key] is None:
        env[key] = default

    return env[key]


def get_headers():
    token = env.get("RAPIDPRO_API_TOKEN")
    if not token:
        raise ValueError("RAPIDPRO_API_TOKEN is missing from environment variables.")
    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }


def get_all_results(endpoint, host, params=None):
    """
    Generator to handle RapidPro API pagination automatically.
    """
    url = f"{host}/api/v2/{endpoint}"
    headers = get_headers()
    
    while url:
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            for result in data.get("results", []):
                yield result
                
            url = data.get("next")
            # Clear params after first request so they aren't duplicated in next_url
            params = None 
        except requests.exceptions.RequestException as e:
            print(f"  [!] Error fetching {endpoint}: {e}")
            break


def chunked_action(endpoint, host, payload_key, item_list, action, extra_data=None):
    """
    Helper to perform bulk actions in chunks.
    """
    if not item_list:
        return

    # Default batch size for RapidPro is usually 100
    BATCH_SIZE = 100
    headers = get_headers()
    url = f"{host}/api/v2/{endpoint}"
    
    print(f"  > Prepared {action} for {len(item_list)} items via {endpoint}...")

    if env.get("dry_run"):
        print(f"    [DRY RUN] Would execute POST to {endpoint} with {len(item_list)} items.")
        return

    for i in range(0, len(item_list), BATCH_SIZE):
        batch = item_list[i:i + BATCH_SIZE]
        payload = {
            "action": action,
            payload_key: batch
        }
        if extra_data:
            payload.update(extra_data)
            
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in [200, 204]:
                print(f"    ✔ Processed batch {i // BATCH_SIZE + 1} ({len(batch)} items)")
            else:
                print(f"    [!] Failed batch {i // BATCH_SIZE + 1}: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"    [!] Request error: {e}")


def get_all_flows_mapping(host):
    """
    Fetches all flows from the API to build a dictionary mapping:
    {'Flow Name': 'Flow UUID'}
    """
    print(f"  > Fetching flow definitions from {host}...")
    flow_mapping = {}
    
    for flow in get_all_results("flows.json", host):
        flow_mapping[flow["name"]] = flow["uuid"]
            
    return flow_mapping


def get_run_stats_for_uuid(host, flow_uuid, flow_name):
    """
    Fetches all runs for a specific flow UUID and counts totals.
    """
    print(f"  > Processing runs for: {flow_name}...")
    
    total_runs = 0
    responded_true_count = 0
    response_values = {"None": 0}
    
    params = {"flow": flow_uuid}
    
    for run in get_all_results("runs.json", host, params=params):
        total_runs += 1
        if run.get("responded") is True:
            responded_true_count += 1
            # Summarize values:
            values = {v["name"]: v["value"] for v in run["values"].values()}
            values = str(dict(sorted(values.items())))
            if values not in response_values.keys():
                response_values[values] = 1
            else:
                response_values[values] += 1
        else:
            response_values["None"] += 1
            
    response_values = dict(sorted(response_values.items()))
    return total_runs, responded_true_count, response_values


def step_count_flow_runs():
    host = getenv("RAPIDPRO_URL")
    target_names_str = safe_getenv("FLOW_NAMES", "")
    target_names = [name.strip() for name in target_names_str.split(",") if name.strip()]

    if not target_names:
        print("  [!] No flow names found in FLOW_NAMES environment variable.")
        return

    # 1. Map Names to UUIDs
    all_flows = get_all_flows_mapping(host)
    results = []

    # 2. Iterate and Count
    for name in target_names:
        uuid = all_flows.get(name)
        
        if uuid:
            total, responded, response_values = get_run_stats_for_uuid(host, uuid, name)
            results.append({
                "Flow Name": name,
                "Flow UUID": uuid,
                "Total Runs": total,
                "Responded True": responded,
                "Responded %": f"{(responded/total*100):.1f}%" if total > 0 else "0%",
                "Response Values": response_values,
            })
        else:
            print(f"  [!] Warning: Could not find UUID for flow named '{name}'")
            results.append({
                "Flow Name": name,
                "Flow UUID": "NOT FOUND",
                "Total Runs": 0,
                "Responded True": 0,
                "Responded %": "N/A",
                "Response Values": "N/A",
            })

    # 3. Output to CSV
    output_filename = safe_getenv("OUTPUT_FILE", "flow_run_stats.csv")

    if ".csv" in output_filename:
        keys = ["Flow Name", "Flow UUID", "Total Runs", "Responded True", "Responded %", "Response Values"]
        
        try:
            with open(output_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows([{k: r.get(k) for k in keys} for r in results])
            print(f"  > Results written to {output_filename}")
        except IOError as e:
            print(f"  [!] Error writing output file: {e}")
    elif "report" in output_filename:
        output = ""

        output += "## Successful Response Quadrant Chart\n"

        success_lambda = lambda item: sum([item["Response Values"][k] for k in item["Response Values"].keys() if "yes" in k or "new" in k or "complete" in k])
        results = [r | {"Successes": success_lambda(r)} for r in results]
        output += f"```mermaid\n{generate_quadrant_chart(results, 'Successes')}\n```\n"
        output += "## Total Response Quadrant Chart\n"
        output += f"```mermaid\n{generate_quadrant_chart(results, 'Responded True')}\n```\n"


        output += f"""\n## Response Type Pie Charts"""
        for pie in generate_pie_charts(results):
            output += f"\n```mermaid\n{pie}\n```"

        output += "\n## Results Table\n"
        L = results
        output+=f"|{'|'.join(L[0])}|\n|{'|'.join('-'*len(k)for k in L[0])}|\n"+''.join(f"|{'|'.join(map(str,d.values()))}|\n"for d in L)
            
        output += f"\n<details>\n<summary>Raw Data</summary>\n\n```\n{results}\n```\n</details>\n"
        try:
            with open(output_filename, "w", newline="", encoding="utf-8") as f:
                f.write(output)
            print(f"  > Results written to {output_filename}")
        except IOError as e:
            print(f"  [!] Error writing output file: {e}")


def step_process_deletion_requests():
    host = getenv("RAPIDPRO_URL")
    target_group_name = safe_getenv("DELETION_REQUEST_GROUP", "deletion request")

    print(f"  > Looking for group '{target_group_name}'...")
    
    # 1. Find the Group UUID
    target_group_uuid = None
    for group in get_all_results("groups.json", host, {"name": target_group_name}):
        if group["name"] == target_group_name:
            target_group_uuid = group["uuid"]
            break
    
    if not target_group_uuid:
        print(f"  [!] Group '{target_group_name}' not found. Aborting.")
        return

    print(f"  > Found Group UUID: {target_group_uuid}")

    # 2. Get Contacts in the group
    print("  > Fetching contacts in group...")
    contacts = list(get_all_results("contacts.json", host, {"group": target_group_uuid}))
    print(f"  > Found {len(contacts)} contacts.")

    if not contacts:
        return

    # Print start info
    print("\n  --- Contacts Queued for Deletion ---")
    print(f"  {'Contact UUID':<40} | {'Created On'}")
    print("  " + "-" * 80)
    for contact in contacts:
        print(f"  {contact['uuid']:<40} | {contact['created_on']}")
    print("  " + "-" * 80 + "\n")

    if env.get("dry_run"):
        print("  [DRY RUN] Skipping artifact collection and deletion steps.")
        return

    all_message_ids = []
    all_run_uuids = []
    contacts_to_delete = []
    deletion_log = []

    # 3. Collect Artifacts (Messages and Runs)
    print("  > Collecting artifacts (Messages/Runs)...")
    for i, contact in enumerate(contacts):
        c_uuid = contact["uuid"]
        c_created = contact["created_on"]
        
        # Get Messages
        msg_count = 0
        for m in get_all_results("messages.json", host, {"contact": c_uuid}):
            all_message_ids.append(m["id"])
            msg_count += 1
            
        # Get Runs
        run_count = 0
        for r in get_all_results("runs.json", host, {"contact": c_uuid}):
            all_run_uuids.append(r["uuid"])
            run_count += 1

        contacts_to_delete.append(c_uuid)
        
        # Prepare log entry
        deletion_log.append({
            "uuid": c_uuid,
            "created_on": c_created,
            "deleted_at": None,
            "status": "PENDING"
        })
        
        if (i + 1) % 10 == 0:
            print(f"    Processed {i + 1}/{len(contacts)} contacts...")

    print(f"  > Artifacts collected: {len(all_message_ids)} messages, {len(all_run_uuids)} runs.")

    # 4. Delete Messages
    failed_msgs = []
    if all_message_ids:
        print(f"  > Deleting {len(all_message_ids)} messages...")
        failed_msgs = chunked_action("message_actions.json", host, "messages", all_message_ids, "delete")
    else:
        print("  > No messages to delete.")

    # 5. Delete Runs
    failed_runs = []
    if all_run_uuids:
        print(f"  > Deleting {len(all_run_uuids)} runs...")
        failed_runs = chunked_action("run_actions.json", host, "runs", all_run_uuids, "delete")
    else:
        print("  > No runs to delete.")

    # --- VERIFICATION STEP ---
    # If any messages or runs failed to delete, we STOP here.
    # This prevents deleting the contact if their data (PII) is still stuck in the system.
    if failed_msgs or failed_runs:
        print("\n  [!] SAFETY STOP: Artifact deletion failed.")
        print(f"      - {len(failed_msgs)} messages failed to delete.")
        print(f"      - {len(failed_runs)} runs failed to delete.")
        print("      Contacts will NOT be deleted to prevent residual orphaned data.")
        print("      Please inspect the logs/errors and re-run.")
        return 

    # 6. Delete Contacts (Only proceeds if above check passed)
    if contacts_to_delete:
        print(f"  > Deleting {len(contacts_to_delete)} contacts...")
        failed_contacts = chunked_action("contact_actions.json", host, "contacts", contacts_to_delete, "delete")
        
        # Update logs
        now = datetime.now().isoformat()
        failed_contact_set = set(failed_contacts)
        
        for log in deletion_log:
            if log["uuid"] in failed_contact_set:
                log["status"] = "FAILED"
            else:
                log["deleted_at"] = now
                log["status"] = "SUCCESS"
    else:
        print("  > No contacts to delete.")

    # 7. Final Table
    print("\n" + "="*90)
    print("DELETION SUMMARY")
    print("="*90)
    print(f"{'Contact UUID':<38} | {'Status':<10} | {'Deleted At'}")
    print("-" * 90)
    for entry in deletion_log:
        status = entry.get("status", "UNKNOWN")
        deleted_at = entry["deleted_at"] or "N/A"
        print(f"{entry['uuid']:<38} | {status:<10} | {deleted_at}")
    print("="*90)


def step_export_contacts():
    host = getenv("RAPIDPRO_URL")
    output_filename = safe_getenv("OUTPUT_FILE", "contacts.csv")
    whitelist_str = safe_getenv("CONTACT_FIELDS", "")
    whitelist_fields = [f.strip() for f in whitelist_str.split(",") if f.strip()]

    print("  > Exporting contact data...")
    print(f"  > Whitelisted fields: {whitelist_fields}")

    # 1. Fetch Groups to create boolean columns
    print("  > Fetching group definitions...")
    groups_mapping = {}  # UUID -> Name
    for group in get_all_results("groups.json", host):
        groups_mapping[group["uuid"]] = group["name"]
    
    sorted_group_names = sorted(groups_mapping.values())
    print(f"  > Found {len(sorted_group_names)} groups for schema.")

    # 2. Prepare CSV Header
    # Base fields + whitelisted fields + group booleans
    header = ["created_on"] + whitelist_fields + sorted_group_names

    # 3. Fetch Contacts and Write to CSV
    print(f"  > Fetching contacts and writing to {output_filename}...")
    try:
        with open(output_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
            writer.writeheader()

            count = 0
            for contact in get_all_results("contacts.json", host):
                row = {
                    "created_on": contact.get("created_on"),
                }

                # Add Whitelisted Fields
                fields = contact.get("fields", {})
                for field in whitelist_fields:
                    row[field] = fields.get(field, "")

                # Add Group Memberships
                contact_group_uuids = set([g['uuid'] for g in contact.get("groups", []) if 'uuid' in g.keys()]) # Set of UUIDs
                for g_uuid, g_name in groups_mapping.items():
                    row[g_name] = g_uuid in contact_group_uuids

                writer.writerow(row)
                count += 1
                if count % 1000 == 0:
                    print(f"    Exported {count} contacts...")

            print(f"  > Finished exporting {count} contacts to {output_filename}.")

    except IOError as e:
        print(f"  [!] Error writing output file: {e}")


def generate_quadrant_chart(data, response_key):
    # 1. Filter out empty runs and calculate Max for Normalization
    valid_data = [d for d in data if d['Total Runs'] > 0]
    max_runs = max(d['Total Runs'] for d in valid_data) if valid_data else 1

    # 2. Start the Mermaid String
    chart = [
        "quadrantChart",
        '    title "Strategy Analysis: Volume vs. Engagement"',
        '    x-axis "Low Volume" --> "High Volume"',
        '    y-axis "Low Response" --> "High Response"',
        '    quadrant-1 "High Impact"',     # Top Right (Mermaid treats Q1 as Top Right)
        '    quadrant-2 "Niche Success"',       # Top Left (Mermaid treats Q2 as Top Left)
        '    quadrant-3 "Low Priority"',        # Bottom Left
        '    quadrant-4 "Missed Opportunity"'   # Bottom Right
    ]

    # 3. Process each item
    for item in valid_data:
        # CLEAN NAME: Remove prefix, title case, and truncate if too long
        raw_name = item['Flow Name'].replace('interaction - ', '').replace('_', ' ').title()
        if len(raw_name) > 15:
            clean_name = raw_name[:12] + ".."
        else:
            clean_name = raw_name
        
        # NORMALIZE X (Volume): 0.0 to 1.0
        # We start X at 0.02 to ensure points aren't squashed against the very edge
        x_val = item['Total Runs'] / max_runs
        if x_val < 0.02: x_val = 0.02
        if x_val > 0.99: x_val = 0.99
        
        # NORMALIZE Y (Response %): 0.0 to 1.0
        y_val = float(item[response_key]) / item['Total Runs']
        if y_val < 0.02: y_val = 0.02
        if y_val > 0.99: y_val = 0.99
        
        # Append formatted line
        chart.append(f'    "{raw_name}": [{x_val:.2f}, {y_val:.2f}]')

    return "\n".join(chart)


def generate_pie_charts(data):
    all_charts = []
    
    for item in data:
        # Skip flows with no runs
        if item['Total Runs'] == 0:
            continue
            
        flow_name = item['Flow Name'].replace('interaction - ', '').replace('_', ' ').title()
        
        # Start Mermaid Pie Block
        chart_code = [f'pie title "{flow_name}"']
        
        # Sort values so largest slices are first (better visual)
        sorted_responses = sorted(item['Response Values'].items(), key=lambda x: x[1], reverse=True)
        
        for key, count in sorted_responses:
            if count > 0:
                label = key.replace('"', "'") # Avoid quote syntax errors
                chart_code.append(f'    "{label}" : {count}')
        
        all_charts.append("\n".join(chart_code))

    return all_charts


step_dict = {
    "count_flow_runs": {
        "fn": step_count_flow_runs,
        "start_msg": "Starting flow run analysis",
        "end_msg": "Flow run analysis complete",
        "required_env": [
            "RAPIDPRO_API_TOKEN",
            "RAPIDPRO_URL",
            "FLOW_NAMES"
        ],
    },
    "process_deletion_requests": {
        "fn": step_process_deletion_requests,
        "start_msg": "Starting deletion request processing",
        "end_msg": "Deletion processing complete",
        "required_env": [
            "RAPIDPRO_API_TOKEN",
            "RAPIDPRO_URL",
        ],
    },
    "export_contacts": {
        "fn": step_export_contacts,
        "start_msg": "Starting contact export",
        "end_msg": "Contact export complete",
        "required_env": [
            "RAPIDPRO_API_TOKEN",
            "RAPIDPRO_URL",
        ]
    }
}


def assert_env_exists(step_list):
    load_dotenv(".env")

    failure_list = []
    for step_name in step_list:
        step = step_dict.get(step_name)
        if not step:
            continue 
            
        try:
            for e in step.get("required_env", []):
                env[e] = getenv(e)
                if env[e] is None:
                    failure_list.append(e)
        except KeyError:
            continue

    if len(failure_list) != 0:
        raise Exception(
            f"Required environment variables not found: {failure_list}\n"
            "Maybe you need a .env file?"
        )


def main(step_list, dry_run: bool = False):
    env["dry_run"] = dry_run
    
    assert_env_exists(step_list)

    print("=" * 50)
    print("🚀 Starting RapidPro Tools Pipeline")
    if dry_run:
        print("   [DRY RUN ENABLED]")
    print("=" * 50)

    for i, step_name in enumerate(step_list):
        if step_name not in step_dict:
            print(f"⚠️  Step '{step_name}' not found. Skipping.")
            continue
            
        step = step_dict[step_name]
        print(f"\n🚀 Step {i+1}: {step['start_msg']}")
        step["fn"]()
        print(f"✅ Step {i+1}: {step['end_msg']}")

    print("\n" + "=" * 50)
    print("🎉 Execution finished!")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A CLI tool for interacting with the RapidPro API."
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run (skips destructive actions like deletes).",
    )

    parser.add_argument(
        "--steps",
        type=str,
        nargs="+",
        default=["count_flow_runs"],
        help=(
            "Space separated list of steps/tools to run.\n"
            f"Options: {[step_name for step_name in step_dict.keys()]}"
        ),
    )

    args = parser.parse_args()

    main(
        step_list=args.steps,
        dry_run=args.dry_run,
    )