from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import json

# Define the exact base API endpoint URL to intercept
API_ENDPOINT = "https://rhmzrs.com/data/feeds/EkoPodaci.json"

# Global container for the data captured from the network response
RAW_DATA_CONTAINER = []

def handle_response(response):
    """Callback function to check network responses for the data endpoint."""
    global RAW_DATA_CONTAINER
    
    # Check if the response URL matches the known API endpoint
    # We use 'in response.url' to handle the dynamic timestamps in the URL
    if API_ENDPOINT in response.url:
        try:
            # Read the JSON response body
            data = response.json()
            
            # The DataTables API typically returns an object with a 'data' key containing the list of rows.
            # We assume the list of rows is either at the root or under the 'data' key.
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
        
        # 2. Wait for the page to navigate and allow all AJAX calls to complete
        page.goto(url)
        page.wait_for_timeout(10000) # Give 10 seconds for the AJAX data transfer to complete
        
        browser.close()

        if not RAW_DATA_CONTAINER:
            print("\n❌ FATAL ERROR: Data feed was not successfully intercepted. Check network conditions.")
            sys.exit(1)

        # 3. Process the captured data (the first captured set is assumed correct)
        raw_rows = RAW_DATA_CONTAINER[0]

        # Define the exact final column names (12 columns total)
        final_column_names = [
            'Вријеме', 'Станица', 'O3', 'CO', 'SО2', 'NO', 
            'NO2', 'NOx', 'PM10', 'PM25', 'H2S', 'C6H6'
        ]

        # Load the raw list of lists into a DataFrame
        final_df = pd.DataFrame(raw_rows)
        print(f"\nSuccessfully loaded {len(final_df)} rows from JSON response.")

        # Ensure we have at least 12 columns and rename them according to the standard
        if final_df.shape[1] >= len(final_column_names):
            # Trim to the required 12 columns and rename
            final_df = final_df.iloc[:, :len(final_column_names)]
            final_df.columns = final_column_names
        else:
            print(f"ERROR: JSON data had {final_df.shape[1]} columns, expected 12. Saving raw data.")
            # If structure is wrong, save the raw DF for inspection
            final_df.columns = [f'Col_{i}' for i in range(final_df.shape[1])]
            

        # 4. Final Save
        output_file = "air_quality_data.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
        print(f"✅ ULTIMATE SUCCESS: Saved {len(final_df)} rows of data to {output_file}")
        print(final_df.head())


if __name__ == "__main__":
    run()
