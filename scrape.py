from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import json
import time # Need to import the time module

# Define the exact base API endpoint URL to intercept
API_ENDPOINT = "https://rhmzrs.com/data/feeds/EkoPodaci.json"

# Global container for the data captured from the network response
RAW_DATA_CONTAINER = []

def handle_response(response):
    """Callback function to check network responses for the data endpoint."""
    global RAW_DATA_CONTAINER
    
    # Check if the response URL matches the known API endpoint
    if API_ENDPOINT in response.url:
        try:
            # Read the JSON response body
            data = response.json()
            
            # Assuming the JSON returns an object with a 'data' key containing the list of rows.
            if isinstance(data, dict) and 'data' in data:
                raw_rows = data['data']
            elif isinstance(data, list):
                raw_rows = data
            else:
                return # Not the expected structure

            if len(raw_rows) >= 7: # We only care if it has the 7+ rows of data
                RAW_DATA_CONTAINER.append(raw_rows)
                print(f"Captured RAW JSON data from: {response.url}")
                
        except Exception as e:
            # Print a debug message if JSON parsing fails for the correct endpoint
            print(f"Failed to parse JSON from API endpoint: {e}")
            pass


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Attach the response handler
        page.on("response", handle_response)
        
        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url} and monitoring network traffic for JSON data...")
        
        # 2. Navigate and wait for AJAX calls to fire
        page.goto(url)

        # 3. CRUCIAL FIX: Wait loop to ensure the asynchronous handler finishes
        timeout_start = time.time()
        print("Waiting for data capture (max 15 seconds)...")

        # Wait until RAW_DATA_CONTAINER is populated or 15 seconds elapse
        while not RAW_DATA_CONTAINER and time.time() < timeout_start + 15:
            # wait_for_timeout is synchronous and ensures the main thread pauses
            page.wait_for_timeout(500) 
        
        browser.close()

        if not RAW_DATA_CONTAINER:
            print("\n❌ FATAL ERROR: Data feed was not successfully intercepted within the timeout.")
            sys.exit(1)

        # 4. Process the captured data
        raw_rows = RAW_DATA_CONTAINER[0]
        final_df = pd.DataFrame(raw_rows)
        print(f"\nSuccessfully loaded {len(final_df)} rows from JSON response.")

        # Define the exact final column names (12 columns total)
        final_column_names = [
            'Вријеме', 'Станица', 'O3', 'CO', 'SО2', 'NO', 
            'NO2', 'NOx', 'PM10', 'PM25', 'H2S', 'C6H6'
        ]

        # 5. Final Cleanup and Save
        if final_df.shape[1] >= len(final_column_names):
            final_df = final_df.iloc[:, :len(final_column_names)]
            final_df.columns = final_column_names
        else:
            print(f"⚠️ WARNING: JSON data had {final_df.shape[1]} columns, expected 12. Saving raw data.")
            final_df.columns = [f'Col_{i}' for i in range(final_df.shape[1])]
            

        output_file = "air_quality_data.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
        print(f"✅ ULTIMATE SUCCESS: Saved {len(final_df)} rows of data to {output_file}")
        print(final_df.head())


if __name__ == "__main__":
    run()
