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

        # FIX: Increased timeout and wait for data rows
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

        # FINAL SOLUTION: Search dynamically for the table that matches the known structure (12 columns)
        target_df = None
        TARGET_COLUMNS = 12
        
        for i, df in enumerate(dfs):
            # We look for 12 columns AND actual data rows (> 1 row total)
            if len(df.columns) == TARGET_COLUMNS and len(df) > 1:
                print(f"SUCCESS: Found data table at index {i}. It has {len(df)} rows.")
                target_df = df
                break
            # Log skipped tables for debugging
            print(f"Skipping table {i}: {len(df)} rows, {len(df.columns)} columns.")

        # Save the result
        if target_df is not None and not target_df.empty and len(target_df) > 1:
            # Clean up: Drop rows that are purely empty
            target_df = target_df.dropna(how='all')
            
            output_file = "air_quality_data.csv"
            target_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"✅ FINAL SUCCESS: Saved data ({len(target_df)} data rows) to {output_file}")
            print(target_df.head())
        else:
            print("FATAL ERROR: Could not find the correct 12-column table with data.")
            sys.exit(1) # Fail the workflow if data is missing


if __name__ == "__main__":
    run()
