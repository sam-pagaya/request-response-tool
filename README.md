# Request Response Tool (RRT)

## 📋 Project Overview
The **RRT** is a localized automation framework designed to generate unique test data, execute API requests through a secure Postman bridge, and reconcile results into a final Excel report.

### The "Why"
Direct API execution from IDEs is restricted in our environment due to permission policies. This tool utilizes **Postman** as a secure execution bridge. Since Postman cannot natively write response data to your local disk, this tool uses a **Node.js sidecar server** to capture, archive, and perform safety backups of your data.



---

## 🏗 The 4-Stage Lifecycle

| Stage | Component | Language | Purpose |
| :--- | :--- | :--- | :--- |
| **1. Generate** | `1-generator/` | Python | Create unique requests from an Excel source. |
| **2. Execute** | **Postman** | JS | Run requests through the secure Sandbox bridge. |
| **3. Archive** | `2-archiver/` | Node.js | Capture and persist filtered responses to disk. |
| **4. Reconcile** | `3-matcher/` | Python | Match inputs to outputs in a final Excel report. |

---

## 🛠 Prerequisites 

### 1. Software Requirements
* **Python 3.x**
* **Node.js (LTS)**
* **Postman Desktop App** (Logged into the shared Team Workspace)

### 2. Dependency Setup
Run the following in your terminal or use the provided `setup.bat`:
```bash
# Install Python dependencies
pip install pandas openpyxl

# Install Node.js dependencies
cd 2-archiver
npm install express
```

---

## 📁 Data Retention & Safety

### The "Logic Gate"
The Postman bridge is programmed to be "smart." It acts as a primary filter to ensure your final datasets are high-quality and actionable:
* **Approved Offers:** Automatically routed to the "Passed" log.
* **Interesting Failures:** Only non-standard declines are captured for QA diagnostics.
* **Auto-Filtered:** The script automatically skips failures caused by *"No credit report found,"* preventing your logs from being cluttered with expected environmental noise.



### Auto-Cleanup & Backups
* **Cleanup:** To ensure every test session is "fresh" and prevent data bleed between runs, the server wipes the active `.json` files every time you shut it down (`Ctrl+C`).
* **The Safety Net:** Before wiping the active data, the server automatically creates a timestamped backup in the `2-archiver/archive/` folder. If you forget to run the Matcher script before closing the server, your data is preserved there for historical retrieval.



---

## ⚠️ Important Rules

* **Local Files Only:** Always select your data file from your **local drive** within the Postman Runner. Using cloud-synced files or web-linked data may cause the bridge connection to fail.
* **Body Formatting:** Ensure the Python generator wraps all requests in a `"body"` key. The Postman pre-request script is specifically hardcoded to look for this key to perform the raw JSON injection into the API call.
* **PII Security:** **Never commit `.xlsx`, `.xls`, or `.json` files to Git.** These contain real PII (Personally Identifiable Information). Always verify that your `.gitignore` is active and correctly configured before pushing any updates to the repository.

---

## 🛠 Troubleshooting & Deep Dives

If you encounter issues or need to modify the core behavior of the tool, please refer to the [**DOCUMENTATION.md**](./DOCUMENTATION.md) file. It contains granular details on:

* **Excel Header Requirements:** Exact naming conventions required for the source data.
* **Randomization Logic:** How income, loan amounts, and terms are calculated.
* **Server Safety Limits:** Instructions on how to adjust `MAX_APPROVED` and `MAX_FAILED` thresholds.