## Code for 994 new NSCID

import requests
import pandas as pd
import time
import random
from concurrent.futures import ThreadPoolExecutor

# Function to fetch SID, Version, and Synonyms from PubChem
def get_pubchem_info(nscid, retries=5, delay_range=(2, 10)):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/substance/name/NSC{nscid}/JSON"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)  # Increased timeout

            if response.status_code == 200:
                data = response.json()
                
                # Extract Substance ID (SID) and Version, prioritizing the latest version
                substances = data.get("PC_Substances", [])
                if substances:
                    latest_substance = max(substances, key=lambda x: x.get("version", 0))  # Get latest version
                    sid = latest_substance.get("sid", "Not Found")
                    version = latest_substance.get("version", "Not Found")
                else:
                    sid, version = "Not Found", "Not Found"

                # Extract synonyms (if available)
                synonyms = latest_substance.get("synonyms", ["Not Found"])
                synonyms_str = ", ".join(synonyms) if isinstance(synonyms, list) else "Not Found"

                # Extract CID using a separate API request
                cid = get_cid_from_pubchem(nscid)

                return {"NSCID": nscid, "SID": sid, "Version": version, "CID": cid, "Synonyms": synonyms_str}

            print(f"Attempt {attempt+1}: Received status {response.status_code}. Retrying...")

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed for NSC{nscid}: {e}")
        
        time.sleep(random.uniform(*delay_range))  # Wait before retrying
    
    print(f"Failed to fetch data for NSC{nscid} after {retries} attempts.")
    return {"NSCID": nscid, "SID": "Not Found", "Version": "Not Found", "CID": "Not Found", "Synonyms": "Not Found"}

# Function to fetch CID separately using the PubChem Compound API
def get_cid_from_pubchem(nscid):
    cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/NSC{nscid}/cids/JSON"
    
    try:
        response = requests.get(cid_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            return cids[0] if cids else "Not Found"  # Return the first CID if available
    except requests.exceptions.RequestException:
        pass  # Ignore errors and return "Not Found"

    return "Not Found"

# Function to process NSC IDs from an Excel file
def process_nscid_list(input_excel, output_excel="output.xlsx"):
    df = pd.read_excel(input_excel, usecols=["NSCID"])  # Read NSCID column

    # Multithreading to speed up API calls
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:  # Adjust thread count
        results = list(executor.map(get_pubchem_info, df["NSCID"]))

    # Convert results to DataFrame
    output_df = pd.DataFrame(results)

    # Save results to Excel
    output_df.to_excel(output_excel, index=False)
    print(f"Results saved to {output_excel}")

# Example Usage
input_file = "c:/Users/anushree/OneDrive - Cellworks/Documents/Training_FINAL/NCI60_GDSC2_17_2_25/NCI60_MAPPING_FINAL_25_FEB25/NCI60_final_mapping.xlsx"
output_file = "c:/Users/anushree/OneDrive - Cellworks/Documents/Training_FINAL/NCI60_GDSC2_17_2_25/NCI60_MAPPING_FINAL_25_FEB25/NCI60_final_mapping_result.xlsx"

process_nscid_list(input_file, output_file)
