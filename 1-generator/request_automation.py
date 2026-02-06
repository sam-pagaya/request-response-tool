import pandas as pd
import random
import string
import requests
import json
import os
import sys
from datetime import datetime
import urllib3
from requests.auth import HTTPBasicAuth

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
DATA_PATH = "/Users/sam.morris/Desktop/RRT/1-generator/selected_users.csv"
API_URL = "https://upstart.sandbox.credit.pagaya-services.com/api/v4/upstart"
OUTPUT_FILE = "/Users/sam.morris/Desktop/RRT/1-generator/responses.json"

AUTH_USER = "pagaya"
AUTH_PASS = "9RbkhvbJc0CY3ftKKGGr"

MAX_APPROVED = 100
MAX_DECLINED = 50

def generate_random_string(length=8):
    return ''.join(random.choices(string.digits, k=length))

def load_data():
    """Load applicant data from selected_users.csv (first_name, last_name, ssn, city, zip, state, dob, full_address)."""
    df = pd.read_csv(DATA_PATH)
    return df

def get_random_pii(df):
    """Pick a random row from the dataframe; selected_users.csv has first_name, last_name, ssn, city, zip, state, dob, full_address."""
    row = df.sample(n=1).iloc[0]
    city = str(row["city"]) if pd.notna(row["city"]) else ""
    state = str(row["state"]) if pd.notna(row["state"]) else ""
    zip_code = str(row["zip"]) if pd.notna(row["zip"]) else ""
    full_address = str(row["full_address"]) if pd.notna(row["full_address"]) else f"{city} {state} {zip_code}".strip()
    dob = str(row["dob"]) if pd.notna(row["dob"]) else "1970-01-01"
    return {
        "first_name": str(row["first_name"]) if pd.notna(row["first_name"]) else "",
        "last_name": str(row["last_name"]) if pd.notna(row["last_name"]) else "",
        "city": city,
        "zip": zip_code,
        "state": state,
        "dob": dob,
        "address": full_address,
        "ssn": "000000000"
    }

def create_request_body(pii_data):
    income_frequency = "MONTHLY"
    income_verified = True
    income_amount = random.randint(50000, 200000)
    
    loan_amount = random.randint(2000, 25000)
    term = random.choice([36, 48, 60])
    partner_app_id = generate_random_string(8)
    
    asset_classes = ["personal_loan", "student_loan", "payday_loan", "mortgage", "auto", "revolving_debt", "other"]
    random_asset_class = random.choice(asset_classes)
    
    # PII object (ssn not sent)
    pii_object = {
        "first_name": pii_data["first_name"],
        "last_name": pii_data["last_name"],
        "city": pii_data["city"],
        "zip": pii_data["zip"],
        "state": pii_data["state"],
        "dob": pii_data["dob"],
        "address": pii_data["address"]
    }
    
    body = {
        "application_data": {
            "main_applicant": {
                "pii": pii_object,
                "income": [
                    {
                        "frequency": income_frequency,
                        "type": "EE",
                        "income_verified": income_verified,
                        "amount": income_amount,
                        "currency": "USD"
                    }
                ],
                "residence_payment": 1500,
                "residence_type": None,
                "cash_advance": "3",
                "employment_status": "TEMP",
                "membership_type": "guest",
                "prior_loans_data": [
                    {
                        "loan_amount": 7000.0,
                        "status": "open",
                        "max_dpd": 7,
                        "issue_date": "2022-02-13",
                        "monthly_payment": 256.4,
                        "balance": 4598,
                        "asset_class": random_asset_class,
                        "term": 36,
                        "partner_application_id": "1234567890"
                    }
                ]
            },
            "partner": {
                "loan_purpose": "A58",
                "decline_reason": ["SAT"],
                "partner_application_id": partner_app_id,
                "user_flow": "CYR"
            }
        },
        "requested_loan_data": {
            "terms": {
                "loan_amount": loan_amount,
                "term": [term]
            },
            "economics": {
                "discounts": [
                    {
                        "discount_name": "DPRC",
                        "discount_type": None,
                        "discount_amount": None
                    }
                ],
                "fees": [
                    {
                        "fee_name": "Origination",
                        "fee_type": "Percentage",
                        "fee_amount": 2
                    }
                ]
            }
        },
        "marketing_referral_source_data": {
            "campaign_id": "7800",
            "referral_source": None,
            "offer_code": None
        }
    }
    return body

def generate_requests_to_file(count=300, output_path=None, pretty_body=False):
    """Generate N random request bodies and write a Postman data file (array of {body: "..."}).
    Use {{body}} in Postman. Optionally pass pretty_body=True for indented body strings.
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", f"postman_requests_{count}.json")
    print(f"Loading data from {DATA_PATH}...")
    df = load_data()
    print(f"Loaded {len(df)} rows")
    requests_list = []
    for i in range(count):
        pii = get_random_pii(df)
        body = create_request_body(pii)
        requests_list.append(body)
        if (i + 1) % 50 == 0:
            print(f"Generated {i + 1}/{count} requests...")
    # Postman body-only format: array of {"body": "<json string>"}
    if pretty_body:
        postman_rows = [{"body": json.dumps(req, indent=2, ensure_ascii=True)} for req in requests_list]
    else:
        postman_rows = [{"body": json.dumps(req, ensure_ascii=True)} for req in requests_list]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(postman_rows, f, indent=2, ensure_ascii=True)
    print(f"Done. Wrote {count} requests to {output_path} (use {{body}} in Postman)")
    return output_path

def build_postman_data_json(requests_path=None, output_path=None):
    """Convert requests JSON to Postman data file with {{variableName}} keys."""
    if requests_path is None:
        requests_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", "requests_300.json")
    if output_path is None:
        output_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", "postman_data.json")
    with open(requests_path, "r") as f:
        data = json.load(f)
    requests_list = data.get("requests", data) if isinstance(data, dict) else data
    postman_rows = []
    for req in requests_list:
        app = req.get("application_data", {})
        main_app = app.get("main_applicant", {})
        pii = main_app.get("pii", {})
        income = (main_app.get("income") or [{}])[0]
        prior = (main_app.get("prior_loans_data") or [{}])[0]
        partner = app.get("partner", {})
        terms = req.get("requested_loan_data", {}).get("terms", {})
        row = {
            "endpointPath": "upstart",
            "first_name": pii.get("first_name", ""),
            "last_name": pii.get("last_name", ""),
            "city": pii.get("city", ""),
            "zip": pii.get("zip", ""),
            "state": pii.get("state", ""),
            "dob": pii.get("dob", ""),
            "address": pii.get("address", ""),
            "income_frequency": income.get("frequency", ""),
            "income_verified": json.dumps(income.get("income_verified", False)),
            "income_amount": income.get("amount", ""),
            "loan_amount": terms.get("loan_amount", ""),
            "term": terms.get("term", [None])[0] if terms.get("term") else "",
            "partner_application_id": partner.get("partner_application_id", ""),
            "asset_class": prior.get("asset_class", ""),
            "requestBody": json.dumps(req),
        }
        postman_rows.append(row)
    with open(output_path, "w") as f:
        json.dump(postman_rows, f, indent=2)
    print(f"Done. Wrote {len(postman_rows)} rows to {output_path}")
    return output_path


    """Convert requests_300.json to Postman data file.
    pretty_body=False: one variable 'body' (minified JSON string) -> use {{body}} in Postman.
    pretty_body=True: one variable 'body' with indented JSON so the file is readable (same content).
    """
    if requests_path is None:
        requests_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", "requests_300.json")
    if output_path is None:
        output_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", "postman_requests_only.json")
    with open(requests_path, "r") as f:
        data = json.load(f)
    requests_list = data.get("requests", data) if isinstance(data, dict) else data
    if pretty_body:
        postman_rows = [{"body": json.dumps(req, indent=2, ensure_ascii=True)} for req in requests_list]
    else:
        postman_rows = [{"body": json.dumps(req, ensure_ascii=True)} for req in requests_list]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(postman_rows, f, indent=2, ensure_ascii=True)
    print(f"Done. Wrote {len(postman_rows)} rows to {output_path} (use {{body}} in Postman)")
    return output_path


    """Convert requests_300.json to Postman data file with same structure as original (array of full request objects). File is large but readable; in Postman use {{application_data}}, {{requested_loan_data}}, {{marketing_referral_source_data}} in body."""
    if requests_path is None:
        requests_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", "requests_300.json")
    if output_path is None:
        output_path = os.path.join(os.path.dirname(OUTPUT_FILE) or ".", "postman_requests_same_structure.json")
    with open(requests_path, "r") as f:
        data = json.load(f)
    requests_list = data.get("requests", data) if isinstance(data, dict) else data
    with open(output_path, "w") as f:
        json.dump(requests_list, f, indent=2)
    print(f"Done. Wrote {len(requests_list)} rows to {output_path}")
    print("  In Postman body (raw JSON) use: {\"application_data\": {{application_data}}, \"requested_loan_data\": {{requested_loan_data}}, \"marketing_referral_source_data\": {{marketing_referral_source_data}}}")
    return output_path

def main():
    print(f"Loading data from {DATA_PATH}...")
    df = load_data()
    print(f"Loaded {len(df)} rows")
    
    approved_count = 0
    declined_count = 0
    
    results = {
        "approved": [],
        "declined": []
    }
    
    # Check if output file exists and load existing counts if needed
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                existing_data = json.load(f)
                results["approved"] = existing_data.get("approved", [])
                results["declined"] = existing_data.get("declined", [])
                approved_count = len(results["approved"])
                declined_count = len(results["declined"])
                print(f"Resuming with {approved_count} approved and {declined_count} declined.")
        except:
            pass

    print("Starting API requests...")
    
    while approved_count < MAX_APPROVED or declined_count < MAX_DECLINED:
        pii = get_random_pii(df)
        request_body = create_request_body(pii)
        
        try:
            # Added explicit headers to match Postman defaults
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "program": "pl_ep"
            }
            response = requests.post(
                API_URL, 
                json=request_body, 
                headers=headers,
                verify=False,
                auth=HTTPBasicAuth(AUTH_USER, AUTH_PASS)
            )
            
            # Treat non-2xx as API/auth errors, not loan decisions
            if not response.ok:
                try:
                    response_data = response.json()
                    msg = response_data.get("Message", response.text[:200])
                except json.JSONDecodeError:
                    msg = response.text[:200]
                print(f"API error (Status {response.status_code}): {msg}")
                if response.status_code == 403 and "explicit deny" in str(msg).lower():
                    print("  -> Check IAM/identity policy: your user/role may be explicitly denied access.")
                continue

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print(f"Error: Response was not JSON. Status code: {response.status_code}")
                print(f"Response text: {response.text[:200]}...")
                continue

            # Determine if approved or declined
            is_approved = False
            
            # Print response for debugging if we only get declines
            if approved_count == 0 and (declined_count + 1) % 5 == 0:
                print(f"Sample response (Status {response.status_code}): {json.dumps(response_data)[:200]}...")

            # Check for decision in offer_decision object
            offers = response_data.get("offers", [])
            if not offers:
                offers = response_data.get("offers_data", [])
            
            if offers:
                for offer in offers:
                    decision_obj = offer.get("offer_decision", {})
                    status = decision_obj.get("decision_status", "").lower()
                    if status == "approved":
                        is_approved = True
                        break
            else:
                decision_obj = response_data.get("offer_decision", {})
                status = decision_obj.get("decision_status", "").lower()
                if status == "approved":
                    is_approved = True
            
            if is_approved:
                if approved_count < MAX_APPROVED:
                    results["approved"].append({
                        "request": request_body,
                        "response": response_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    approved_count += 1
                    print(f"Approved: {approved_count}/{MAX_APPROVED}")
            else:
                if declined_count < MAX_DECLINED:
                    results["declined"].append({
                        "request": request_body,
                        "response": response_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    declined_count += 1
                    print(f"Declined: {declined_count}/{MAX_DECLINED}")
            
            # Print status every 10 requests
            if (approved_count + declined_count) % 10 == 0:
                print(f"Status: {approved_count} Approved, {declined_count} Declined")
            
            # Save progress periodically
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(results, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
                
        except Exception as e:
            print(f"Error during request: {e}")
            
        if approved_count >= MAX_APPROVED and declined_count >= MAX_DECLINED:
            break

    print(f"Finished! Saved {approved_count} approved and {declined_count} declined responses to {OUTPUT_FILE}")

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1].lower() == "generate":
        args = [a for a in sys.argv[2:] if a != "--pretty"]
        pretty = "--pretty" in sys.argv
        n = int(args[0]) if len(args) > 0 else 300
        out = args[1] if len(args) > 1 else None
        generate_requests_to_file(count=n, output_path=out, pretty_body=pretty)
    elif len(sys.argv) >= 2 and sys.argv[1].lower() == "postman":
        req_path = sys.argv[2] if len(sys.argv) > 2 else None
        out_path = sys.argv[3] if len(sys.argv) > 3 else None
        build_postman_data_json(requests_path=req_path, output_path=out_path)
    elif len(sys.argv) >= 2 and sys.argv[1].lower() == "postman-body":
        args = [a for a in sys.argv[2:] if a != "--pretty"]
        pretty = "--pretty" in sys.argv
        req_path = args[0] if len(args) > 0 else None
        out_path = args[1] if len(args) > 1 else None
        build_postman_body_only(requests_path=req_path, output_path=out_path, pretty_body=pretty)
    elif len(sys.argv) >= 2 and sys.argv[1].lower() == "postman-same":
        req_path = sys.argv[2] if len(sys.argv) > 2 else None
        out_path = sys.argv[3] if len(sys.argv) > 3 else None
        build_postman_same_structure(requests_path=req_path, output_path=out_path)
    else:
        main()
