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

        # FINAL FIX: Target the specific table index (0) as requested
        TABLE_INDEX = 0 
        
        if len(dfs) > TABLE_INDEX:
            target_df = dfs[TABLE_INDEX]
            # Print the exact row count for clarity to prove if data is present
            print(f"Targeted table index {TABLE_INDEX} with {len(target_df.columns)} columns. Found {len(target_df)} rows.")
        else:
            print(f"Error: Targeted index {TABLE_INDEX} not found in the {len(dfs)} tables.")
            sys.exit(1)

        # Save the result
        if not target_df.empty and len(target_df) > 1:
            # Clean up: Drop rows that are purely empty
            target_df = target_df.dropna(how='all')
            
            output_file = "air_quality_data.csv"
            target_df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"SUCCESS: Saved data ({len(target_df)} data rows) to {output_file}")
            print(target_df.head())
        else:
            # If the log shows 0 rows, this message confirms the issue
            print("ERROR: Target table (Table 0) was empty or contained only a header. The data must be in another table (e.g., Table 1).")


if __name__ == "__main__":
    run()
