from playwright.sync_api import sync_playwright
import pandas as pd
import sys

def run():
    with sync_playwright() as p:
        print("Launching browser...")
        # Ensure we are running headless for GitHub Actions
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url}...")
        page.goto(url)

        # FIX: Increased timeout and wait for data rows
        try:
            print("Waiting for table data to load (45s timeout)...")
            # Wait for a table cell (td) to appear in the table body (tbody)
            page.wait_for_selector("table tbody tr td", timeout=45000) 
        except Exception as e:
            # This is the block that handles timeouts and exits with error code 1
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
            print(f"Found {len(dfs)} tables on the page. PRINTING CONTENT TO LOG FOR INSPECTION.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # FINAL DEBUGGING STEP: Print the content of all found tables to the log
        # This will show us the exact index of the correct table.
        for i, df in enumerate(dfs):
            print(f"\n--- DEBUG: Table {i} ---")
            print(f"Dimensions: {len(df)} rows, {len(df.columns)} columns")
            
            if df.empty:
                print("Content: EMPTY DATAFRAME")
            elif len(df) == 1:
                print("Content: Only HEADER ROW found.")
                print(df.to_string())
            else:
                print("Content: Found potential data.")
                # Use .to_string() to prevent data truncation in the log
                print(df.head(10).to_string()) 
        
        # The script exits successfully here, so Git will find 'nothing to commit'
        # but the vital debugging information will be in the log.
        print("\n--- END OF SCRAPER RUN ---")


if __name__ == "__main__":
    run()
