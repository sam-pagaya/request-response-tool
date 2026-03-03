import pandas as pd
import random
import string
import json
import os
import sys

def generate_random_string(length=8):
    return "".join(random.choices(string.digits, k=length))

def load_project_config(project_name):
    """Loads the template and mapping rules for a specific partner."""
    base_path = os.path.join("projects", project_name)
    
    with open(os.path.join(base_path, "template.json"), 'r') as f:
        template = json.load(f)
        
    with open(os.path.join(base_path, "mapping.json"), 'r') as f:
        mapping = json.load(f)
        
    return template, mapping

def fill_template(template_str, pii_row, mapping, co_pii_row=None):
    """Replaces placeholders in the template string with actual data."""
    # 1. Fill Dynamic Data from CSV (main applicant)
    for placeholder, csv_column in mapping.get("dynamic", {}).items():
        val = str(pii_row[csv_column]) if pd.notna(pii_row[csv_column]) else ""
        template_str = template_str.replace(placeholder, val)

    # 2. Fill Co-Applicant PII from CSV (different row)
    if co_pii_row is not None:
        for placeholder, csv_column in mapping.get("dynamic_co_applicant", {}).items():
            val = str(co_pii_row[csv_column]) if pd.notna(co_pii_row[csv_column]) else ""
            template_str = template_str.replace(placeholder, val)

    # 3. Handle Randomized Logic
    for placeholder, rules in mapping.get("randomized", {}).items():
        if rules["type"] == "int":
            lo, hi = int(rules["range"][0]), int(rules["range"][1])
            val = str(random.randint(lo, hi))
        elif rules["type"] == "float":
            lo, hi = float(rules["range"][0]), float(rules["range"][1])
            val = str(round(random.uniform(lo, hi), 2))
        elif rules["type"] == "choice":
            val = str(random.choice(rules["options"]))
        elif rules["type"] == "string_digits":
            val = generate_random_string(rules["length"])
        
        template_str = template_str.replace(placeholder, val)
        
    return json.loads(template_str)

def generate_requests(project_name, count=10):
    # Pathing based on your uploaded structure
    csv_path = "selected_users.csv"
    df = pd.read_csv(csv_path)
    
    template_obj, mapping = load_project_config(project_name)
    template_str = json.dumps(template_obj)
    
    final_output = []
    for _ in range(count):
        # Main applicant and co-applicant: two different rows from CSV
        if len(df) < 2:
            pii_row = co_pii_row = df.sample(n=1).iloc[0]
        else:
            two_rows = df.sample(n=2, replace=False)
            pii_row = two_rows.iloc[0]
            co_pii_row = two_rows.iloc[1]
        body_content = fill_template(template_str, pii_row, mapping, co_pii_row=co_pii_row)
        
        # Wrap in the "body" key for Postman compatibility
        final_output.append({
            "body": json.dumps(body_content)
        })
        
    output_filename = f"postman_{project_name}_{count}.json"
    with open(output_filename, "w") as f:
        json.dump(final_output, f, indent=2)
        
    print(f"✅ Generated {count} requests for '{project_name}' -> {output_filename}")

if __name__ == "__main__":
    # Usage: python universal_generator.py upstart 50
    proj = sys.argv[1] if len(sys.argv) > 1 else "upstart"
    num = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    generate_requests(proj, num)