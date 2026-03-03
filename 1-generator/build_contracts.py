"""
Build contract application payloads from archived Postman (approved) responses.

Reads an archive JSON (e.g. from 2-archiver), uses project-specific contract
template + mapping to fill contract call JSON from each response, and writes
a single output file with all ready contract calls.

Usage:
  python build_contracts.py <project_name> <archive_file> [--output <path>] [--requests <path>]

  --requests  Optional. Postman request JSON (array of { "body": "<json string>" }).
              When provided, vehicle (year, mileage, wholesale_value) and applicant
              income are taken from the request; join is by partner_application_id.

Example:
  python build_contracts.py exeter 2-archiver/archive/2026-02-19T14-23-09-896Z_all_approved_results.json
  python build_contracts.py exeter 2-archiver/archive/..._all_approved_results.json --requests postman_exeter_500.json --output contracts_exeter.json
"""

import json
import os
import sys
import copy
from datetime import date


def get_nested(data, path):
    """Get value at dot-separated path; supports numeric segments for list index."""
    if not path:
        return data
    parts = path.split(".")
    current = data
    for part in parts:
        if part.isdigit():
            current = current[int(part)]
        else:
            current = current[part]
    return current


def set_nested(obj, path, value):
    """Set value at dot-separated path; creates dicts/lists as needed."""
    parts = path.split(".")
    current = obj
    for i, part in enumerate(parts[:-1]):
        key = int(part) if part.isdigit() else part
        next_key = parts[i + 1]
        next_is_index = next_key.isdigit()
        if key not in current:
            current[key] = [] if next_is_index else {}
        current = current[key]
    last = parts[-1]
    current[int(last) if last.isdigit() else last] = value


def deep_replace(template, replacements):
    """Replace placeholders in template (recursive). Template is dict/list/str/number."""
    if isinstance(template, dict):
        return {k: deep_replace(v, replacements) for k, v in template.items()}
    if isinstance(template, list):
        return [deep_replace(item, replacements) for item in template]
    if isinstance(template, str) and template in replacements:
        return replacements[template]
    return template


def coerce_numeric(contract, numeric_keys):
    """Walk contract and coerce listed keys to int/float where possible."""
    if isinstance(contract, dict):
        for k, v in contract.items():
            if k in numeric_keys and isinstance(v, (str, int, float)):
                try:
                    if isinstance(v, float) or (isinstance(v, str) and "." in v):
                        contract[k] = float(v)
                    else:
                        contract[k] = int(v)
                except (ValueError, TypeError):
                    pass
            else:
                coerce_numeric(v, numeric_keys)
    elif isinstance(contract, list):
        for item in contract:
            coerce_numeric(item, numeric_keys)


def load_contract_config(project_name):
    """Load contract_template.json and contract_mapping.json for a project."""
    base = os.path.join(os.path.dirname(__file__), "Projects", project_name)
    template_path = os.path.join(base, "contract_template.json")
    mapping_path = os.path.join(base, "contract_mapping.json")
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Contract template not found: {template_path}")
    if not os.path.isfile(mapping_path):
        raise FileNotFoundError(f"Contract mapping not found: {mapping_path}")
    with open(template_path, "r") as f:
        template = json.load(f)
    with open(mapping_path, "r") as f:
        mapping = json.load(f)
    return template, mapping


def build_one_contract(response, template, mapping, request_body=None, contract_date=None):
    """Build a single contract payload from one archive response (and optional request)."""
    response_paths = mapping.get("response_paths", {})
    request_paths = mapping.get("request_paths", {})
    defaults = mapping.get("defaults", {})
    numeric_fields = mapping.get("numeric_fields", [])

    replacements = dict(defaults)
    if contract_date is None:
        contract_date = str(date.today())
    replacements["{{contract_date}}"] = contract_date

    for placeholder, path in response_paths.items():
        try:
            value = get_nested(response, path)
            replacements[placeholder] = value
        except (KeyError, IndexError, TypeError):
            if placeholder in defaults:
                replacements[placeholder] = defaults[placeholder]

    if request_body is not None:
        for placeholder, path in request_paths.items():
            try:
                value = get_nested(request_body, path)
                replacements[placeholder] = value
            except (KeyError, IndexError, TypeError):
                pass  # request-sourced only; no default fallback

    contract = deep_replace(copy.deepcopy(template), replacements)
    coerce_numeric(contract, numeric_fields)
    return contract


def load_requests_by_partner_id(requests_path):
    """Load Postman-style request file and return dict[partner_application_id] = parsed body."""
    with open(requests_path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    by_id = {}
    for row in data:
        body_str = row.get("body") if isinstance(row, dict) else None
        if not body_str:
            continue
        try:
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
            pid = get_nested(body, "partner.partner_application_id")
            if pid is not None:
                by_id[str(pid)] = body
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return by_id


def build_contracts(project_name, archive_path, output_path=None, requests_path=None):
    """Load archive, build one contract per approved result, write output file."""
    template, mapping = load_contract_config(project_name)

    request_paths = mapping.get("request_paths", {})
    if request_paths and not requests_path:
        print(
            "Error: This project's contract_mapping has request_paths (vehicle/income from request). "
            "Pass --requests <path> to the Postman request file (e.g. postman_exeter_500.json).",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(archive_path, "r") as f:
        archive = json.load(f)

    if not isinstance(archive, list):
        archive = [archive]

    requests_by_id = {}
    if requests_path and os.path.isfile(requests_path):
        requests_by_id = load_requests_by_partner_id(requests_path)
    elif requests_path:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt_requests = os.path.join(repo_root, requests_path)
        if os.path.isfile(alt_requests):
            requests_by_id = load_requests_by_partner_id(alt_requests)

    require_request_match = bool(request_paths and requests_path)

    contracts = []
    skipped_no_request = 0
    for item in archive:
        response = item.get("response")
        if not response:
            continue
        offers = response.get("offers_data") or []
        if not offers or offers[0].get("offer_decision", {}).get("decision_status") != "Approved":
            continue
        partner_id = response.get("application_data", {}).get("partner_application_id")
        request_body = requests_by_id.get(str(partner_id)) if partner_id else None
        if require_request_match and request_body is None:
            skipped_no_request += 1
            continue
        contract = build_one_contract(response, template, mapping, request_body=request_body)
        contracts.append(contract)
    if skipped_no_request:
        print(f"⚠ Skipped {skipped_no_request} approved result(s) with no matching request (use --requests with same run).")

    if output_path is None:
        base_name = os.path.splitext(os.path.basename(archive_path))[0]
        output_path = os.path.join(
            os.path.dirname(__file__),
            f"contract_calls_{project_name}_{base_name}.json"
        )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(contracts, f, indent=2)

    print(f"Built {len(contracts)} contract call(s) -> {output_path}")
    return output_path


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip())
        sys.exit(1)
    project_name = sys.argv[1]
    archive_path = sys.argv[2]
    output_path = None
    requests_path = None
    if "--output" in sys.argv:
        i = sys.argv.index("--output")
        if i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    if "--requests" in sys.argv:
        i = sys.argv.index("--requests")
        if i + 1 < len(sys.argv):
            requests_path = sys.argv[i + 1]
    if not os.path.isfile(archive_path):
        # Try relative to repo root (parent of 1-generator) when run from 1-generator
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt_path = os.path.join(repo_root, archive_path)
        if os.path.isfile(alt_path):
            archive_path = alt_path
        else:
            print(f"Archive file not found: {archive_path}", file=sys.stderr)
            sys.exit(1)
    build_contracts(project_name, archive_path, output_path, requests_path)


if __name__ == "__main__":
    main()
