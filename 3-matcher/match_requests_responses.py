"""
Standalone script: read a requests JSON file and a responses JSON file,
match by partner_application_id, and output an Excel file with two columns:
requests and responses (one row per matching pair).
"""
import json
import pandas as pd
import sys
import os


def get_partner_id_from_request(item):
    """Extract partner_application_id from a request item (postman body string or full object)."""
    req_obj = None
    if isinstance(item, dict):
        if "body" in item:
            try:
                body = item["body"]
                req_obj = json.loads(body) if isinstance(body, str) else body
            except (json.JSONDecodeError, TypeError):
                return None, None
        else:
            req_obj = item
    if not req_obj:
        return None, None
    partner = (req_obj.get("application_data") or {}).get("partner") or {}
    pid = partner.get("partner_application_id")
    if pid is not None:
        pid = str(pid).strip()
    return pid, req_obj


def get_partner_id_from_response(item):
    """Extract partner_application_id from a response item. Response has application_data.partner_application_id."""
    if not isinstance(item, dict):
        return None, None
    resp = item.get("response") if "response" in item else item
    if not isinstance(resp, dict):
        return None, None
    app_data = resp.get("application_data") or {}
    pid = app_data.get("partner_application_id")
    if pid is not None:
        pid = str(pid).strip()
    return pid, resp


def load_requests(path):
    """Load requests file; return list of (partner_application_id, request_object)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "requests" in data:
        items = data["requests"]
    elif isinstance(data, list):
        items = data
    else:
        items = []
    out = []
    for item in items:
        pid, req_obj = get_partner_id_from_request(item)
        if pid:
            out.append((pid, req_obj))
    return out


def load_responses(path):
    """Load responses file; return list of (partner_application_id, response_object)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = []
    out = []
    for item in data:
        pid, resp_obj = get_partner_id_from_response(item)
        if pid:
            out.append((pid, resp_obj))
    return out


def match_and_export(requests_path, responses_path, output_excel_path=None):
    """
    Read requests and responses JSON, match by partner_application_id,
    write Excel with columns 'requests' and 'responses' (JSON strings per row).
    """
    requests_list = load_requests(requests_path)
    responses_list = load_responses(responses_path)

    by_id_requests = {pid: req for pid, req in requests_list}
    by_id_responses = {pid: resp for pid, resp in responses_list}

    common_ids = sorted(set(by_id_requests) & set(by_id_responses))

    rows = []
    for pid in common_ids:
        req_obj = by_id_requests[pid]
        resp_obj = by_id_responses[pid]
        rows.append({
            "requests": json.dumps(req_obj, ensure_ascii=True),
            "responses": json.dumps(resp_obj, ensure_ascii=True),
        })

    df = pd.DataFrame(rows, columns=["requests", "responses"])
    if output_excel_path is None:
        base = os.path.splitext(requests_path)[0]
        output_excel_path = base + "_matched_results.xlsx"
    df.to_excel(output_excel_path, index=False)
    print(f"Matched {len(rows)} request/response pairs by partner_application_id.")
    print(f"Wrote: {output_excel_path}")
    return output_excel_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python match_requests_responses.py <requests.json> <responses.json> [output.xlsx]")
        sys.exit(1)
    requests_path = sys.argv[1]
    responses_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    match_and_export(requests_path, responses_path, output_path)
