import requests
import pandas as pd
import sys
import json

# The API endpoint identified from the network traffic
API_ENDPOINT = "https://rhmzrs.com/data/feeds/EkoPodaci.json"

def run():
    print(f"Attempting to fetch data directly from API: {API_ENDPOINT}")
    
    try:
        # 1. Fetch data directly via HTTP request
        response = requests.get(API_ENDPOINT, timeout=30)
        response.raise_for_status() 
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ FATAL ERROR: Direct API call failed (Network/Timeout issue). Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\n❌ FATAL ERROR: Response was not valid JSON.")
        sys.exit(1)

    # 2. Extract the data from the known key: 'trenutni'
    if 'trenutni' not in data or not isinstance(data['trenutni'], dict):
        print("\n❌ FATAL ERROR: Could not find the expected 'trenutni' key in the JSON response.")
        sys.exit(1)
        
    # The 'trenutni' key contains a dictionary where keys are station short names (Banjaluka, Brod, etc.) 
    # and the values are the data records. We extract all values.
    raw_records = list(data['trenutni'].values())
    
    if not raw_records:
        print("\n❌ FATAL ERROR: The 'trenutni' data was empty.")
        sys.exit(1)

    print(f"Successfully extracted {len(raw_records)} records from the 'trenutni' object.")

    # 3. Create DataFrame from the list of dictionaries (records)
    final_df = pd.DataFrame(raw_records)

    # 4. Cleanup and Format (Ensure columns are ordered correctly as per your target output)
    
    # We drop Lat/Lon as they were not in the requested output, and ensure 'vrijeme' is first.
    if 'Lat' in final_df.columns:
        final_df = final_df.drop(columns=['Lat', 'Lon'])
    
    # Define the final expected column order
    expected_order = [
        "vrijeme", "stanica", "O3", "CO", "SO2", "NO", 
        "NO2", "NOx", "PM10", "PM2.5", "H2S", "C6H6"
    ]
    
    # Filter and reorder columns that exist in the DataFrame
    final_cols = [col for col in expected_order if col in final_df.columns]
    final_df = final_df[final_cols]

    # Rename columns to the final expected Serbian headers
    final_df = final_df.rename(columns={
        "vrijeme": "Вријеме",
        "stanica": "Станица",
        "PM2.5": "PM25"  # Standardize for output
    })


    # Final Save
    output_file = "air_quality_data.csv"
    final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
    
    print(f"\n✅ ULTIMATE SUCCESS: Saved {len(final_df)} rows to {output_file} via direct API call.")
    print("\n--- Final Data Preview ---")
    print(final_df.head())
    print("--------------------------")


if __name__ == "__main__":
    run()
