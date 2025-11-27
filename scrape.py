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
            # Read without headers, forcing column indices 0, 1, 2
            dfs = pd.read_html(html, header=None)
            print(f"Found {len(dfs)} tables on the page.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # --- FINAL SOLUTION: Search data cells for pollutant names and large size ---
        RAW_DATA_INDEX = -1
        
        for i, df in enumerate(dfs):
            rows = len(df)
            cols = len(df.columns)

            # Rule 1: Must be the 3-column raw data format and large size
            if cols != 3 or rows < 45:
                continue
            
            # Rule 2 (THE FINAL CHECK): The second column (index 1) must contain pollutant codes (PM10, O3, NOX).
            try:
                # Check if the column contains at least one known pollutant code string
                col_content = df.iloc[:, 1].astype(str)
                
                if col_content.str.contains('PM10|SO2|NOX|O3|CO|C6H6').any():
                    RAW_DATA_INDEX = i
                    break # Found the table!
                        
            except Exception:
                # Ignore tables where this check fails
                continue
        
        if RAW_DATA_INDEX == -1:
            print("FATAL ERROR: Could not find the 3-column raw data table by checking for pollutant codes in data cells.")
            sys.exit(1)

        raw_df = dfs[RAW_DATA_INDEX]
        print(f"Targeted raw data table found at Index {RAW_DATA_INDEX} (Pollutant Data Source). Found {len(raw_df)} rows.")

        # Data Transformation (Pivot)
        if not raw_df.empty:
            
            # 1. CRITICAL CLEANUP: Drop the first 3 rows to eliminate headers/titles/garbage
            if len(raw_df) > 3:
                raw_df = raw_df.iloc[3:].reset_index(drop=True) 
            
            # 2. Assign numeric indices (0, 1, 2)
            raw_df.columns = [0, 1, 2] 
            raw_df = raw_df.dropna(subset=[0, 1])
            
            # 3. Pivot the table to the final 12-column format
            final_df = raw_df.pivot_table(
                index=[0],       # Column 0: Station/Time identifier
                columns=[1],     # Column 1: Parameter Name (New column headers)
                values=[2],      # Column 2: Value 
                aggfunc='first'
            ).reset_index()
            
            # 4. Final Cleanup and Rename
            final_column_names = ['Станица/Вријеме', 'C6H6', 'CO', 'H2S', 'NO', 'NO2', 'NOx', 'O3', 'PM10', 'PM25', 'SО2'] 
            final_df.columns = [col[1] if isinstance(col, tuple) else col for col in final_df.columns.values]
            final_df = final_df.rename(columns={0: 'Станица/Вријеме'}) 
            
            print(f"Successfully pivoted cleaned data into {len(final_df)} wide rows.")
            
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
