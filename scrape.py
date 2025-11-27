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

        # Wait for the data to populate the HTML source
        try:
            print("Waiting for data tables to load (15s timeout)...")
            page.wait_for_selector("table tbody tr td", timeout=15000) 
        except Exception:
            print("Warning: Table data did not fully load, proceeding to parse available HTML.")

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

        # FINAL TARGET: Table Index 3 (The 45-row raw data source)
        TABLE_INDEX = 3
        
        if len(dfs) <= TABLE_INDEX:
            print(f"FATAL ERROR: Index {TABLE_INDEX} not found.")
            sys.exit(1)

        raw_df = dfs[TABLE_INDEX]
        print(f"Targeted raw data table at index {TABLE_INDEX}. Found {len(raw_df)} rows.")

        # Data Transformation (Pivot)
        if len(raw_df.columns) == 3 and not raw_df.empty and len(raw_df) > 5:
            
            # 1. Use numeric indices (0, 1, 2) for columns
            raw_df.columns = [0, 1, 2] 
            raw_df = raw_df.dropna(subset=[0, 1])
            
            # 2. Pivot the table: Group the 45 rows by Station (Col 0)
            final_df = raw_df.pivot_table(
                index=[0],       # Column 0: Station/Time identifier (The final rows)
                columns=[1],     # Column 1: Parameter Name (The final columns: PM10, O3, etc.)
                values=[2],      # Column 2: Value 
                aggfunc='first'
            ).reset_index()
            
            # 3. Fix MultiIndex and rename the identifier column
            final_df.columns = [col[1] if isinstance(col, tuple) else col for col in final_df.columns.values]
            final_df = final_df.rename(columns={0: 'Станица/Вријеме'}) 
            
            print(f"Successfully pivoted 45 rows into {len(final_df)} wide rows.")
            
        else:
            print(f"ERROR: Raw data table at index {TABLE_INDEX} was not the expected 3-column format.")
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
