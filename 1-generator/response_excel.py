"""
Match requests (from universal_generator output) with approved responses (from 2-archiver
all_approved_results.json) by partner_application_id, and write an Excel file with
two columns. Each cell contains the full payload:
  - Request: the entire request body (full JSON).
  - Response: the entire response payload (full JSON).
No summarization—whole request and whole response per row.
"""
import json
import os
import sys


def get_partner_application_id_from_request(body_obj):
    """Extract partner_application_id from a parsed request body. Tries common paths."""
    if not isinstance(body_obj, dict):
        return None
    # e.g. exeter: partner.partner_application_id
    pid = body_obj.get("partner", {}).get("partner_application_id")
    if pid is not None:
        return str(pid).strip()
    # e.g. upstart: application_data.partner.partner_application_id
    app = body_obj.get("application_data", {})
    if isinstance(app, dict):
        pid = app.get("partner", {}).get("partner_application_id")
        if pid is not None:
            return str(pid).strip()
    return None


def get_partner_application_id_from_response(response_obj):
    """Extract partner_application_id from a single response (the 'response' payload)."""
    if not isinstance(response_obj, dict):
        return None
    app = response_obj.get("application_data", {})
    if isinstance(app, dict):
        pid = app.get("partner_application_id")
        if pid is not None:
            return str(pid).strip()
    return None


def load_requests(request_file_path):
    """
    Load request file (universal_generator format: array of {body: "<json string>"}).
    Returns list of (partner_application_id, full_request_json_string).
    Each request string is the entire body, pretty-printed for readability in Excel.
    """
    with open(request_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = data if isinstance(data, list) else data.get("requests", [])
    out = []
    for row in rows:
        body_str = row.get("body") if isinstance(row, dict) else None
        if body_str is None:
            continue
        try:
            body_obj = json.loads(body_str)
        except json.JSONDecodeError:
            continue
        pid = get_partner_application_id_from_request(body_obj)
        if pid is not None:
            # Store whole request as pretty-printed JSON so the cell contains the full payload
            full_request_str = json.dumps(body_obj, indent=2, ensure_ascii=True)
            out.append((pid, full_request_str))
    return out


def load_responses(results_file_path):
    """
    Load all_approved_results.json (array of {iteration, timestamp, response}).
    Returns dict: partner_application_id -> full response JSON string (entire response payload).
    """
    with open(results_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else []
    out = {}
    for item in items:
        resp = item.get("response") if isinstance(item, dict) else None
        if resp is None:
            continue
        pid = get_partner_application_id_from_response(resp)
        if pid is not None:
            # Whole response as pretty-printed JSON for the cell
            out[pid] = json.dumps(resp, indent=2, ensure_ascii=True)
    return out


def build_matched_rows(requests_list, responses_by_id):
    """Return list of (full_request_str, full_response_str) for each matched pair. No summarization."""
    rows = []
    for pid, request_str in requests_list:
        response_str = responses_by_id.get(pid)
        if response_str is not None:
            rows.append((request_str, response_str))
    return rows


def write_excel(rows, output_path):
    """Write to Excel: each cell contains the full request or full response JSON (no truncation of payload)."""
    import pandas as pd

    df = pd.DataFrame(rows, columns=["Request", "Response"])
    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Wrote {len(df)} matched request/response pairs to {output_path}")


def run(request_file_path, results_file_path, output_path=None):
    if output_path is None:
        base = os.path.splitext(request_file_path)[0]
        output_path = f"{base}_matched_responses.xlsx"

    requests_list = load_requests(request_file_path)
    responses_by_id = load_responses(results_file_path)
    rows = build_matched_rows(requests_list, responses_by_id)
    write_excel(rows, output_path)
    return output_path


if __name__ == "__main__":
    # Default paths relative to 1-generator
    script_dir = os.path.dirname(os.path.abspath(__file__))
    archiver_dir = os.path.join(os.path.dirname(script_dir), "2-archiver")
    default_requests = os.path.join(script_dir, "postman_exeter_500.json")
    default_results = os.path.join(archiver_dir, "all_approved_results.json")

    request_file = sys.argv[1] if len(sys.argv) > 1 else default_requests
    results_file = sys.argv[2] if len(sys.argv) > 2 else default_results
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    if output_file is None:
        output_file = os.path.join(
            script_dir,
            f"{os.path.splitext(os.path.basename(request_file))[0]}_matched_responses.xlsx",
        )

    run(request_file, results_file, output_file)
