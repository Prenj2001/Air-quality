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
            # This extracts ALL tables from the page into a list
            dfs = pd.read_html(html)
            print(f"Found {len(dfs)} tables on the page.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # FINAL SOLUTION: Target the 3-column table (Index 3) for the raw data
        TABLE_INDEX = 3
        
        if len(dfs) > TABLE_INDEX:
            raw_df = dfs[TABLE_INDEX]
            print(f"Targeted raw data table at index {TABLE_INDEX}. Found {len(raw_df)} rows.")
        else:
            print(f"Error: Targeted index {TABLE_INDEX} not found in the {len(dfs)} tables.")
            sys.exit(1)

        # Data Transformation (Pivot)
        if len(raw_df.columns) == 3 and not raw_df.empty:
            
            # 1. Rename columns based on likely structure (Station, Parameter, Value)
            raw_df.columns = ['Station', 'Parameter', 'Value']
            
            # 2. Drop any rows with missing values (e.g., footers, empty cells)
            raw_df = raw_df.dropna(subset=['Station', 'Parameter'])
            
            # 3. Pivot the table: Use 'Station' as rows, 'Parameter' as columns, and 'Value' as data
            final_df = raw_df.pivot_table(
                index='Station', 
                columns='Parameter', 
                values='Value', 
                aggfunc='first'
            ).reset_index()
            
            print(f"Successfully pivoted data to {len(final_df)} wide rows.")
            
        else:
            print("ERROR: Table 3 was not the expected 3-column raw data format.")
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
