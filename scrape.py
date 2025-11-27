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
        except ValueError:print("Parsing HTML with pandas...")
        try:
            # This extracts ALL tables from the page into a list
            dfs = pd.read_html(html)
            print(f"Found {len(dfs)} tables on the page. PRINTING CONTENT TO LOG FOR INSPECTION.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        # DEBUGGING: Print the content of all found tables to the log
        for i, df in enumerate(dfs):
            print(f"\n--- DEBUG: Table {i} ---")
            print(f"Dimensions: {len(df)} rows, {len(df.columns)} columns")
            
            if df.empty:
                print("Content: EMPTY DATAFRAME")
            elif len(df) == 1:
                print("Content: Only HEADER ROW found.")
                # Use to_string() to avoid truncation
                print(df.to_string())
            else:
                print("Content: Found potential data.")
                print(df.head(10).to_string()) # Print up to 10 rows
        
        # We exit successfully here, ensuring the log is captured.
        print("\n--- END OF SCRAPER RUN ---")

if __name__ == "__main__":
    run()
        
        # --- Start of the final reporting block ---
        if saved_count > 0:
            print("---")
            print(f"SUCCESS: Saved {saved_count} debug files. Please check your repository for the CSV containing the air quality data.")
        else:
            print("FAILURE: No non-empty tables were found for debugging.")
