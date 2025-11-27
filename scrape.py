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

        # FINAL WAIT FIX: Wait for the 8th <tr> element (Header + 7 data rows) in the first table
        try:
            print("Waiting for the 7 data rows to load (60s timeout)...")
            # This selector explicitly targets the 8th row of the first table on the page
            page.wait_for_selector("table:nth-of-type(1) > tbody > tr:nth-of-type(8)", timeout=60000) 
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

        # FINAL TARGET: Table 0 (the 12-column structure)
        TABLE_INDEX = 0 
        
        if len(dfs) > TABLE_INDEX:
            final_df = dfs[TABLE_INDEX]
            print(f"Targeted 12-column table at index {TABLE_INDEX}. Found {len(final_df)} rows.")
        else:
            print(f"Error: Targeted index {TABLE_INDEX} not found in the {len(dfs)} tables.")
            sys.exit(1)

        # Save the result
        if len(final_df.columns) == 12 and len(final_df) > 7:
            
            # Clean up: Drop rows that are purely empty
            final_df = final_df.dropna(how='all')
            
            output_file = "air_quality_data.csv"
            final_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"✅ FINAL SUCCESS: Saved data ({len(final_df)} rows) to {output_file}")
            print(final_df.head())
        else:
            print(f"ERROR: Table 0 was found, but had the wrong size ({len(final_df)} rows) or columns ({len(final_df.columns)}).")
            sys.exit(1)


if __name__ == "__main__":
    run()
