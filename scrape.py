from playwright.sync_api import sync_playwright
import pandas as pd
import sys
import time

def run():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Going to {url}...")
        page.goto(url)

        # Wait for general table content to appear (15s should be sufficient)
        try:
            print("Waiting for any table data to load (15s timeout)...")
            page.wait_for_selector("table tbody tr td", timeout=15000) 
        except Exception as e:
            print(f"WARNING: No table data loaded within timeout. Proceeding to parse available HTML. {e}")

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

        print("\n--- FINAL DEBUG LOG: TABLE CONTENTS ---")
        
        # Iterate through all found tables and print their details
        for i, df in enumerate(dfs):
            rows = len(df)
            cols = len(df.columns)
            
            # Print summary for all tables
            print(f"TABLE INDEX {i}: {rows} rows, {cols} columns.")
            
            # Only print the content of small tables (potential candidates)
            if rows > 0 and rows < 20: 
                print(f"--- CONTENT OF TABLE {i} ---")
                print(df.to_string())
                print("--------------------------")
        
        print("---------------------------------------")
        
        # Exit successfully to ensure the log is captured
        sys.exit(0)


if __name__ == "__main__":
    run()
