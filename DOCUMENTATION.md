# Technical Wiki: Request Response Tool (RRT)

This document provides the granular technical logic for the RRT components. It is intended for users who need to modify the code, update data mappings, or troubleshoot logic gates.

---

## 1. Python Data Generator (`/1-generator`)

### Excel-to-JSON Mapping
The generator relies on a strict contract with the input Excel file. The following headers must exist in the source spreadsheet for the script to function:

| Excel Header | JSON Mapping Path | Logic/Transformation |
| :--- | :--- | :--- |
| `SSN` | N/A | **Filter Gate:** Only rows where SSN is exactly `0` are processed. |
| `House#` | `pii.address` | Combined with street, city, state, and zip. |
| `Street name` | `pii.address` | Combined into the "Full Address" string. |
| `First name` | `pii.first_name` | Direct string conversion. |
| `Last name` | `pii.last_name` | Direct string conversion. |



### Business Logic & Randomization
To ensure varied test results, the following fields are randomized per request:
* **Income:** Assigned using `random.randint(50000, 200000)`.
* **Loan Amount:** Assigned using `random.randint(2000, 25000)`.
* **Term:** Randomly selected from the set `[36, 48, 60]`.
* **Partner App ID:** A unique 8-character string generated for every request to act as the **Primary Key** for reconciliation.

---

## 2. Postman Intelligence Layer

The Postman **Tests** script acts as an intelligent filter to ensure only relevant data is archived to your local machine.

### The Logic Gate
The script inspects the `offers_data` array returned by the API:
1. **Approval Logic:** If `decision_status === "Approved"`, the full response is routed to `localhost:3000/save`.
2. **Rejection Logic:** * The script checks the `decision_drivers`. 
    * If the driver is **"No credit report found"**, the script ignores the response to avoid logging "expected" failures.
    * All other rejection reasons are routed to `localhost:3000/save-failed`.



### The `{{body}}` Injection
The API request body in Postman is set to a variable `{{body}}`. 
* **The Pre-request Script:** It pulls the raw JSON string from your data file and assigns it to this variable. 
* **The Benefit:** This ensures that complex JSON (including nested arrays and objects) is sent exactly as generated, avoiding common Postman string-escaping errors.

---

## 3. Sidecar Archiver (`/2-archiver`)

### Storage Management
The server is configured with safety limits to prevent runaway disk usage:
* `MAX_APPROVED = 100` (Max entries in `all_approved_results.json`)
* `MAX_FAILED = 10` (Max entries in `all_failed_results.json`)

### Safety Archive & Shutdown
The server utilizes Node's `process.on` to listen for shutdown signals (`SIGINT` / `Ctrl+C`):
1. **Backup:** It triggers `backupFiles()`, copying active results to the `/archive` folder with a unique timestamp.
2. **Reset:** It then overwrites the active files with an empty array `[]` to prepare for the next user's session.



---

## 4. Data Matcher (`/3-matcher`)

### The Reconciliation Join
The Matcher script performs a logical "Inner Join" between the initial generated requests and the final captured responses.

* **Primary Key:** `partner_application_id`.
* **The Process:** 1. Loads all generated requests into a lookup dictionary.
    2. Loads all captured responses into a lookup dictionary.
    3. Identifies IDs present in **both** sets.
    4. Serializes the matching objects into a side-by-side Excel format.



### Historical Matching
If you need to match data from a previous session, you can point the matcher at a specific file in the `/archive` folder:
```bash
python 3-matcher/matcher.py 1-generator/requests.json 2-archiver/archive/TIMESTAMPED_FILE.json