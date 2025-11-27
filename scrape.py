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

        # CRITICAL FIX 1: Increase timeout and wait for data rows
        try:
            print("Waiting for table data to load (45s timeout)...")
            page.wait_for_selector("table tbody tr td", timeout=45000) 
        except Exception as e:
            # This is the block that triggers Exit Code 1 if a timeout occurs
            print(f"FATAL ERROR: Table data did not load within timeout. {e}")
            page.screenshot(path="debug_error.png") # Screenshot saved for manual check
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

        # CRITICAL FIX 2: Simplified Logic to find the correct table
        # We assume the data table is the first one found that has more than 5 columns.
        target_df = None
        for i, df in enumerate(dfs):
            # The data table has at least 10 columns (Time, Station, O3, CO, SO2, etc.)
            if len(df.columns) > 5 and len(df) > 1:
                print(f"Assuming table {i} is the target data table (has {len(df.columns)} columns).")
                target_df = df
                break
        
        # Save the result
        if target_df is not None and not target_df.empty:
            # Clean up: Drop rows that are purely empty
            target_df = target_df.dropna(how='all')
            
            output_file = "air_quality_data.csv"
            target_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"SUCCESS: Saved data ({len(target_df)} rows) to {output_file}")
            print(target_df.head())
        else:
            print("ERROR: Found tables, but none matched the criteria (e.g., were empty or too small).")
            # This will result in a successful run but no commit, which is the correct outcome for empty data.


if __name__ == "__main__":
    run()
