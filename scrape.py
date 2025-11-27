from playwright.sync_api import sync_playwright
import pandas as pd
import sys

def run():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url}...")
        page.goto(url)

        # Increased timeout and wait for data rows
        try:
            print("Waiting for table data to load (45s timeout)...")
            page.wait_for_selector("table tbody tr td", timeout=45000) 
        except Exception as e:
            print(f"FATAL ERROR: Table data did not load within timeout. {e}")
            page.screenshot(path="debug_error.png")
            browser.close()
            sys.exit(1)

        # Get the full page HTML
        html = page.content()
        browser.close()

        print("Parsing HTML with pandas...")
        try:
            dfs = pd.read_html(html)
            print(f"Found {len(dfs)} tables on the page.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # Search for the 12-column table structure, which is the user's required output table
        TABLE_INDEX = -1
        TARGET_COLUMNS = 12
        
        for i, df in enumerate(dfs):
            if len(df.columns) == TARGET_COLUMNS:
                TABLE_INDEX = i
                print(f"Found 12-column structure at Index {TABLE_INDEX}.")
                break
        
        if TABLE_INDEX == -1:
            print("FATAL ERROR: Could not find any table with 12 columns.")
            sys.exit(1)

        # --- PROCESS THE RAW DATA SOURCE INSTEAD ---
        # Since the 12-column table is empty, we must find the table with the data (max rows).
        max_rows = 0
        RAW_DATA_INDEX = -1
        
        for i, df in enumerate(dfs):
            # We look for the largest table that has at least 5 rows (to exclude headers/footers)
            if len(df) > max_rows and len(df) > 5:
                max_rows = len(df)
                RAW_DATA_INDEX = i
        
        if RAW_DATA_INDEX == -1:
            print("FATAL ERROR: Could not find any raw data table with more than 5 rows.")
            sys.exit(1)

        print(f"Using raw data source found at Index {RAW_DATA_INDEX} ({max_rows} rows).")
        raw_df = dfs[RAW_DATA_INDEX]

        # Data Transformation (Robust Pivot using numeric indices)
        if len(raw_df.columns) == 3 and not raw_df.empty:
            
            # Use numeric indices (0, 1, 2) for columns
            raw_df.columns = [0, 1, 2] 
            raw_df = raw_df.dropna(subset=[0, 1])
            
            # Pivot the table: 
            final_df = raw_df.pivot_table(
                index=[0],       
                columns=[1],     
                values=[2],      
                aggfunc='first'
            ).reset_index()
            
            # Fix MultiIndex and rename the identifier column
            final_df.columns = [col[1] if isinstance(col, tuple) else col for col in final_df.columns.values]
            final_df = final_df.rename(columns={0: 'Станица/Вријеме'}) 
            
            print(f"Successfully pivoted data to {len(final_df)} wide rows.")
            
        else:
            print(f"ERROR: Raw data table at index {RAW_DATA_INDEX} was not the expected 3-column format.")
            sys.exit(1)

        # Save the result
        if not final_df.empty:
            output_file = "air_quality_data.csv"
            final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"✅ FINAL SUCCESS: Saved data ({len(final_df)} wide rows) to {output_file}")
            print(final_df.head())
        else:
            print("FATAL ERROR: The final pivoted table was empty.")
            sys.exit(1)


if __name__ == "__main__":
    run()
