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
            print(f"Found {len(dfs)} tables on the page. SAVING ALL FOR DEBUGGING.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # DEBUGGING: Loop through ALL found tables and save them if they aren't empty
        saved_count = 0
        for i, df in enumerate(dfs):
            # We only save tables that have at least 2 rows (header + 1 data row)
            if not df.empty and len(df) > 1:
                # Create a descriptive filename: debug_table_INDEX_columnCOUNT.csv
                output_file = f"debug_table_{i}_cols_{len(df.columns)}.csv"
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"✅ Saved potential data table {i} ({len(df.columns)} columns) as {output_file}")
                saved_count += 1
            else:
                print(f"➖ Skipped table {i} as it was empty or too small.")
        
        # --- Start of the final reporting block ---
        if saved_count > 0:
            print("---")
            print(f"SUCCESS: Saved {saved_count} debug files. Please check your repository for the CSV containing the air quality data.")
        else:
            print("FAILURE: No non-empty tables were found for debugging.")
