from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import numpy as np

def run():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url}...")
        page.goto(url)

        try:
            print("Waiting for data tables to load (15s timeout)...")
            page.wait_for_selector("table tbody tr td", timeout=15000) 
        except Exception:
            print("Warning: Table data did not fully load, proceeding to parse available HTML.")

        html = page.content()
        browser.close()

        print("Parsing HTML with pandas...")
        try:
            # Let Pandas infer headers to find the pollutant names
            dfs = pd.read_html(html)
            print(f"Found {len(dfs)} tables on the page.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # --- FINAL SOLUTION: Search for the table containing pollutant identifiers ---
        RAW_DATA_INDEX = -1
        
        for i, df in enumerate(dfs):
            # Convert columns to string and check if pollutants exist
            header_str = " ".join(df.columns.astype(str)).upper()
            
            # Check for key pollutant names known to be in the raw data headers
            if ("PM10" in header_str or "SO2" in header_str or "NOX" in header_str) and len(df.columns) == 3 and len(df) >= 45:
                RAW_DATA_INDEX = i
                break
        
        if RAW_DATA_INDEX == -1:
            print("FATAL ERROR: Could not find the raw data table containing pollutant names (PM10/SO2) in the headers.")
            sys.exit(1)

        raw_df = dfs[RAW_DATA_INDEX]
        print(f"Targeted raw data table found at Index {RAW_DATA_INDEX} (Pollutant-ID Source). Found {len(raw_df)} rows.")

        # Data Transformation (Pivot)
        if not raw_df.empty:
            
            # 1. Reset columns to numeric indices, assuming Pandas read the header row correctly
            # The header row contains the pollutant names, which is correct for the pivot.
            
            # 2. Pivot the table: Group by the first column (Station/Time)
            final_df = raw_df.pivot_table(
                index=raw_df.columns[0],       # Station/Time identifier
                columns=raw_df.columns[1],     # Parameter Name (New column headers)
                values=raw_df.columns[2],      # Value 
                aggfunc='first'
            ).reset_index()
            
            # 3. Rename the first column to match the expected output
            final_df = final_df.rename(columns={final_df.columns[0]: 'Станица/Вријеме'}) 
            
            print(f"Successfully pivoted {len(raw_df)} rows into {len(final_df)} wide rows.")
            
        else:
            print("ERROR: Raw data table was found but was empty.")
            sys.exit(1)

        # Save the result
        if not final_df.empty:
            output_file = "air_quality_data.csv"
            final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"✅ ULTIMATE SUCCESS: Saved {len(final_df)} wide rows to {output_file}")
            print(final_df.head())
        else:
            print("FATAL ERROR: The final pivoted table was empty.")
            sys.exit(1)


if __name__ == "__main__":
    run()
