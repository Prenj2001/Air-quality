import requests
import pandas as pd
import sys

# The API endpoint identified from the network traffic
API_ENDPOINT = "https://rhmzrs.com/data/feeds/EkoPodaci.json"

def run():
    print(f"Attempting to fetch data directly from API: {API_ENDPOINT}")
    
    try:
        # 1. Fetch data directly via HTTP request
        response = requests.get(API_ENDPOINT, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes
        
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ FATAL ERROR: Direct API call failed (Network/Timeout issue).")
        print(f"Error: {e}")
        sys.exit(1)
        
    # 2. Extract raw rows from the JSON (data is usually a list or under a 'data' key)
    if isinstance(data, dict) and 'data' in data:
        raw_rows = data['data']
    elif isinstance(data, list):
        raw_rows = data
    else:
        print("\n❌ FATAL ERROR: JSON structure was unexpected.")
        sys.exit(1)
        
    if not raw_rows or len(raw_rows) < 5:
        print(f"\n❌ FATAL ERROR: Successfully fetched JSON, but it contains too few rows ({len(raw_rows)}).")
        sys.exit(1)

    raw_df = pd.DataFrame(raw_rows)
    print(f"Successfully fetched {len(raw_df)} rows directly from the API.")

    # 3. Apply pivot transformation (assuming API data structure matches the 3-column narrow format)
    if len(raw_df.columns) == 3:
        raw_df.columns = [0, 1, 2]
        raw_df = raw_df.dropna(subset=[0, 1])

        # Pivot to the desired 12-column wide format
        final_df = raw_df.pivot_table(
            index=[0],
            columns=[1],
            values=[2],
            aggfunc='first'
        ).reset_index()

        final_df.columns = [col[1] if isinstance(col, tuple) else col for col in final_df.columns.values]
        final_df = final_df.rename(columns={0: 'Станица/Вријеме'})
        
    else:
        # If the API returns the data already in wide format, save it directly
        final_df = raw_df
        final_df.columns = ['Станица/Вријеме', 'O3', 'CO', 'SО2', 'NO', 'NO2', 'NOx', 'PM10', 'PM25', 'H2S', 'C6H6']
        print("API data was pre-pivoted (wide format).")

    # Final Save
    output_file = "air_quality_data.csv"
    final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
    print(f"✅ ULTIMATE SUCCESS: Saved {len(final_df)} rows to {output_file} via direct API call.")
    print(final_df.head())


if __name__ == "__main__":
    run()
