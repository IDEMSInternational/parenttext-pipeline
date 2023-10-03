import json
import os


def update_expiration_time(config, source, in_fp):
    with open(config.special_expiration, 'r') as specifics_json:
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
