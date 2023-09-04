import json


def update_expiration_time(in_fp, default, specifics_fp, out_fp):
    with open(specifics_fp, 'r') as specifics_json:
        specifics = json.load(specifics_json)

    with open(in_fp, "r") as in_json:
        org = json.load(in_json)

    for flow in org.get("flows", []):
        set_expiration(flow, default, specifics)

    with open(out_fp, "w") as out_json:
        json.dump(org, out_json)


def set_expiration(flow, default, specifics={}):
    expiration = specifics.get(flow["name"], default)

    flow["expire_after_minutes"] = expiration

    if "expires" in flow.get("metadata", {}):
        flow["metadata"]["expires"] = expiration

    return flow
