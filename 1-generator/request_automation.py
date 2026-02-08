import pandas as pd
import random
import string
import json
import os
import sys

# Configuration
DATA_PATH = "/Users/sam.morris/Desktop/RRT/1-generator/selected_users.csv"
OUTPUT_DIR = os.path.dirname(DATA_PATH) or "."


def generate_random_string(length=8):
    return "".join(random.choices(string.digits, k=length))


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
    full_address = (
        str(row["full_address"])
        if pd.notna(row["full_address"])
        else f"{city} {state} {zip_code}".strip()
    )
    dob = str(row["dob"]) if pd.notna(row["dob"]) else "1970-01-01"
    return {
        "first_name": str(row["first_name"]) if pd.notna(row["first_name"]) else "",
        "last_name": str(row["last_name"]) if pd.notna(row["last_name"]) else "",
        "city": city,
        "zip": zip_code,
        "state": state,
        "dob": dob,
        "address": full_address,
        "ssn": "000000000",
    }


def create_request_body(pii_data):
    income_frequency = "MONTHLY"
    income_verified = True
    income_amount = random.randint(50000, 200000)

    loan_amount = random.randint(2000, 25000)
    term = random.choice([36, 48, 60])
    partner_app_id = generate_random_string(8)

    asset_classes = [
        "personal_loan",
        "student_loan",
        "payday_loan",
        "mortgage",
        "auto",
        "revolving_debt",
        "other",
    ]
    random_asset_class = random.choice(asset_classes)

    # PII object (ssn not sent)
    pii_object = {
        "first_name": pii_data["first_name"],
        "last_name": pii_data["last_name"],
        "city": pii_data["city"],
        "zip": pii_data["zip"],
        "state": pii_data["state"],
        "dob": pii_data["dob"],
        "address": pii_data["address"],
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
                        "currency": "USD",
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
                        "partner_application_id": "1234567890",
                    }
                ],
            },
            "partner": {
                "loan_purpose": "A58",
                "decline_reason": ["SAT"],
                "partner_application_id": partner_app_id,
                "user_flow": "CYR",
            },
        },
        "requested_loan_data": {
            "terms": {"loan_amount": loan_amount, "term": [term]},
            "economics": {
                "discounts": [
                    {
                        "discount_name": "DPRC",
                        "discount_type": None,
                        "discount_amount": None,
                    }
                ],
                "fees": [
                    {
                        "fee_name": "Origination",
                        "fee_type": "Percentage",
                        "fee_amount": 2,
                    }
                ],
            },
        },
        "marketing_referral_source_data": {
            "campaign_id": "7800",
            "referral_source": None,
            "offer_code": None,
        },
    }
    return body


def generate_requests_to_file(count=300, output_path=None, pretty_body=False):
    """Generate N random request bodies and write a Postman data file (array of {body: "..."}).
    Use {{body}} in Postman. Optionally pass pretty_body=True for indented body strings.
    """
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, f"postman_requests_{count}.json")
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
        postman_rows = [
            {"body": json.dumps(req, indent=2, ensure_ascii=True)}
            for req in requests_list
        ]
    else:
        postman_rows = [
            {"body": json.dumps(req, ensure_ascii=True)} for req in requests_list
        ]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(postman_rows, f, indent=2, ensure_ascii=True)
    print(f"Done. Wrote {count} requests to {output_path} (use {{body}} in Postman)")
    return output_path


if __name__ == "__main__":
    # Usage: python request_automation.py [generate] [count] [output_path] [--pretty]
    if len(sys.argv) >= 2 and sys.argv[1].lower() == "generate":
        args = [a for a in sys.argv[2:] if a != "--pretty"]
    else:
        args = [a for a in sys.argv[1:] if a != "--pretty"]
    pretty = "--pretty" in sys.argv
    n = int(args[0]) if len(args) > 0 else 300
    out = args[1] if len(args) > 1 else None
    generate_requests_to_file(count=n, output_path=out, pretty_body=pretty)
