## 🚀 Execution Guide (SOP)

### Step 1: Start the Sidecar
Before doing anything else, open a terminal in the `2-archiver` folder and run:
```bash
node server.js
```
### Step 2: Generate Test Data

Run the generator script to pull data from your Excel source and create the requests.json file.

Bash
```bash
python 1-generator/generator.py
```



### Step 3: Postman Automation

1.  Open the **Sandbox** collection in Postman.
    
2.  Right-click the folder (e.g., **Upstart API**) and select **Run collection**.
    
3.  **Filter API Calls:** Unselect all checkboxes, then select **only** the specific API call you are testing.
    
4.  **Load Data:** Click **Select File** and upload the requests.json you generated in Step 2.
    
5.  **Run:** Click the orange **Run Sandbox** button.
    

### Step 4: Final Reconciliation

Once Postman finishes the run, execute the Matcher script to create your final Excel deliverable:

Bash
``` bash
python 3-matcher/matcher.py 1-generator/requests.json 2-archiver/all_approved_results.json
```