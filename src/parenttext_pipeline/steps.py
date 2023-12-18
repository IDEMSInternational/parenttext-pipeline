import json
import os
from copy import copy
from pathlib import Path

from parenttext_pipeline.extract_keywords import batch


def update_expiration_time(config, source, in_fp):
    with open(config.special_expiration, "r") as specifics_json:
        specifics = json.load(specifics_json)

    with open(in_fp, "r") as in_json:
        org = json.load(in_json)

    for flow in org.get("flows", []):
        set_expiration(flow, config.default_expiration, specifics)

    out_fp = os.path.join(
        config.outputpath,
        source["filename"] + "_1_2_modified_expiration_times.json",
    )
    with open(out_fp, "w") as out_json:
        json.dump(org, out_json)

    print("Expiration times modified")

    return out_fp


def set_expiration(flow, default, specifics={}):
    expiration = specifics.get(flow["name"], default)

    flow["expire_after_minutes"] = expiration

    if "expires" in flow.get("metadata", {}):
        flow["metadata"]["expires"] = expiration

    return flow


def split_rapidpro_json(config, source, in_fp):
    n = source.get("split_no", 1)

    if n < 2:
        print(f"File splitting skipped, batch_count={n}")
        return

    with open(in_fp, 'r', encoding='utf-8') as in_json:
        org = json.load(in_json)

    flows_per_file = len(org["flows"]) // n

    for i, b in enumerate(batch(org["flows"], flows_per_file), start=1):
        org_new = copy(org)
        org_new.update(
            {
                "campaigns": [
                    edited
                    for campaign in org["campaigns"]
                    if (edited := edit_campaign(campaign, b))
                ],
                "flows": b,
                "triggers": [
                    trigger
                    for trigger in org["triggers"]
                    if trigger["flow"]["uuid"] in [flow["uuid"] for flow in b]
                ],
            }
        )
        in_path = Path(in_fp)
        out_fp = in_path.with_stem(in_path.stem + "_" + str(i))

        with open(out_fp, "w") as out_file:
            json.dump(org_new, out_file, indent=2)
            print(f"File written, path={out_fp}")


def edit_campaign(campaign, flows):
    if not campaign["events"]:
        return campaign

    campaign_new = copy(campaign)
    campaign_new["events"] = []
    for event in campaign["events"]:
        event_type = event["event_type"]
        flow_name = event["flow"]["name"]
        if event_type in ["F", "M"] and flow_name in [f["name"] for f in flows]:
            campaign_new["events"].append(event)
        else:
            print(
                f"Campaign event removed, campaign={campaign['name']}, "
                f"event_type={event_type}"
            )
            if event_type == "F":
                print(f"Flow not found, name={flow_name}")

    if campaign_new["events"]:
        return campaign_new
