from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import json

# Placeholder for the data captured from the network
RAW_DATA_CONTAINER = []

def handle_response(response):
    """Callback function to check network responses for the data endpoint."""
    global RAW_DATA_CONTAINER
    
    # Check if the URL contains keywords typical of data feeds,
    # or the DataTable server-side processing URL.
    if "/data" in response.url.lower() or "/json" in response.url.lower() or "kontrola" in response.url.lower():
        try:
            # Read the JSON response body
            data = response.json()
            # If the data looks like a large list or dictionary, save it.
            if isinstance(data, dict) and 'data' in data: # Common DataTables structure
                if len(data['data']) > 5:
                    RAW_DATA_CONTAINER.append(data['data'])
                    print(f"Captured RAW JSON data from: {response.url}")
            elif isinstance(data, list) and len(data) > 5:
                RAW_DATA_CONTAINER.append(data)
                print(f"Captured RAW JSON data from: {response.url}")
                
        except Exception:
            # Ignore non-JSON responses
            pass


def run():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Attach the response handler
        page.on("response", handle_response)
        
        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url} and monitoring network traffic...")
        
        # 2. Wait for the page to navigate and the data transfer to complete
        page.goto(url)
        page.wait_for_timeout(10000) # Give 10 seconds for all AJAX calls to complete
        
        browser.close()

        if not RAW_DATA_CONTAINER:
            print("\n❌ FATAL ERROR: No data feed was intercepted.")
            print("Please inspect your browser's Network tab for the exact API URL and provide it.")
            sys.exit(1)

        # Assuming the captured data is the raw list of rows
        raw_rows = RAW_DATA_CONTAINER[0]

        # 3. Load the raw data into Pandas
        # The data should already be in the 12-column format (or close to it)
        final_df = pd.DataFrame(raw_rows)
        print(f"\nSuccessfully loaded {len(final_df)} rows from JSON response.")

        # 4. Final Cleanup and Save
        # Assuming the JSON returns the columns in the correct order, we just need to rename them.
        final_df.columns = [
            'Вријеме', 'Станица', 'O3', 'CO', 'SО2', 'NO', 
            'NO2', 'NOx', 'PM10', 'PM25', 'H2S', 'C6H6'
        ]
        
        # Remove any extra columns if the JSON returned more than 12
        final_df = final_df.iloc[:, :12]
        
        output_file = "air_quality_data.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
        print(f"✅ ULTIMATE SUCCESS: Saved {len(final_df)} rows of 12-column data to {output_file}")
        print(final_df.head())


if __name__ == "__main__":
    run()
