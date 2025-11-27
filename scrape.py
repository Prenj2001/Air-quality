from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import json

# Define the exact base API endpoint URL to intercept
API_ENDPOINT_PATTERN = "EkoPodaci.json"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url} and waiting for the data feed...")
        
        # 1. Navigate to the page
        page.goto(url)
        
        # 2. Synchronously wait for the specific JSON response
        try:
            print(f"Waiting for response matching '{API_ENDPOINT_PATTERN}' (60s timeout)...")
            
            # This pauses execution until the response URL contains the required file name
            response = page.wait_for_response(
                lambda r: API_ENDPOINT_PATTERN in r.url,
                timeout=60000
            )
            
            # 3. Read the JSON body directly from the intercepted response
            data = response.json()
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR: Data feed was not successfully intercepted. Timeout occurred: {e}")
            browser.close()
            sys.exit(1)
        
        browser.close()

        # Assuming the JSON returns an object with a 'data' key containing the list of rows
        if isinstance(data, dict) and 'data' in data:
            raw_rows = data['data']
        elif isinstance(data, list):
            raw_rows = data
        else:
            print("\n❌ FATAL ERROR: Intercepted data was not in the expected format (list or dict with 'data' key).")
            print(f"Sample of unexpected data: {str(data)[:200]}...")
            sys.exit(1)

        # 4. Process the captured data
        final_df = pd.DataFrame(raw_rows)
        print(f"\nSuccessfully loaded {len(final_df)} rows from JSON response.")

        # Define the exact final column names (12 columns total)
        final_column_names = [
            'Вријеме', 'Станица', 'O3', 'CO', 'SО2', 'NO', 
            'NO2', 'NOx', 'PM10', 'PM25', 'H2S', 'C6H6'
        ]

        # 5. Final Cleanup and Save
        if final_df.shape[1] >= len(final_column_names):
            # Trim to the required 12 columns and rename
            final_df = final_df.iloc[:, :len(final_column_names)]
            final_df.columns = final_column_names
        else:
            print(f"⚠️ WARNING: JSON data had {final_df.shape[1]} columns, expected 12.")
            # If structure is wrong, save with generic names for inspection
            final_df.columns = [f'Col_{i}' for i in range(final_df.shape[1])]
            

        output_file = "air_quality_data.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
        print(f"✅ ULTIMATE SUCCESS: Saved {len(final_df)} rows of data to {output_file}")
        print(final_df.head())


if __name__ == "__main__":
    run()
