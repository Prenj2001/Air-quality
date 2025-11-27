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

        # CRITICAL FIX: Wait for the actual DATA rows to appear, not just the table
        # We wait for a table cell (td) that is inside a table body
        try:
            print("Waiting for table data to load...")
            page.wait_for_selector("table tbody tr td", timeout=20000)
        except Exception as e:
            print(f"Error: Table data did not load within timeout. {e}")
            # Capture screenshot for debugging (viewable in GitHub Actions artifacts if configured)
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

        # Logic to find the CORRECT table
        # We look for the table that contains the 'PM10' column
        target_df = None
        for i, df in enumerate(dfs):
           # Logic to find the CORRECT table
        # We assume the main data table is the first one found that has more than 5 columns and more than 1 row.
        target_df = None
        for i, df in enumerate(dfs):
            # Check for sufficient columns (e.g., Time, Station, O3, CO, etc., which is > 5)
            # and ensure it has data rows (len(df) > 1)
            if len(df.columns) > 5 and len(df) > 1:
                print(f"Assuming table {i} is the target data table (has {len(df.columns)} columns).")
                target_df = df
                break
        
        if target_df is not None and not target_df.empty:
            # Clean up: Drop rows that are purely empty
            target_df = target_df.dropna(how='all')
            
            output_file = "air_quality_data.csv"
            target_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"SUCCESS: Saved data to {output_file}")
            print(target_df.head()) # Print first few rows to the log
        else:
            print("ERROR: Found tables, but none contained 'PM10' or they were empty.")
            # Print the first table just to see what we got
            if dfs:
                print("First table content preview:")
                print(dfs[0].head())

if __name__ == "__main__":
    run()
