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

        try:
            print("Waiting for data tables to load (15s timeout)...")
            page.wait_for_selector("table tbody tr td", timeout=15000) 
        except Exception:
            print("Warning: Table data did not fully load, proceeding to parse available HTML.")

        html = page.content()
        browser.close()

        print("Parsing HTML with pandas...")
        try:
            # Read without headers, to see all raw cells
            dfs = pd.read_html(html, header=None)
            print(f"Found {len(dfs)} tables on the page.")
        except ValueError:
            print("No tables found in the HTML.")
            sys.exit(1)

        print("\n--- FINAL DEBUG LOG: 3-COLUMN TABLE CONTENT ---")
        
        # Iterate through all found tables and check column count
        for i, df in enumerate(dfs):
            rows = len(df)
            cols = len(df.columns)
            
            if cols == 3 and rows >= 10: # Focus on 3-column tables with meaningful size
                print(f"\nTABLE INDEX {i}: {rows} rows, {cols} columns.")
                
                # Print the content of the crucial second column (index 1), which should hold pollutant names
                print(f"--- COLUMN 1 (INDEX 1) CONTENT DUMP ---")
                
                # Print the unique values or the first 20 rows of the column content
                unique_values = df.iloc[:, 1].astype(str).unique()
                if len(unique_values) < 50:
                    print("Unique values:")
                    print(unique_values)
                else:
                    print("First 20 rows:")
                    print(df.iloc[:20, 1].to_string(index=False))
                    
                print("------------------------------------------")
        
        print("----------------------------------------------")
        
        # Exit successfully to ensure the log is captured
        sys.exit(0)


if __name__ == "__main__":
    run()
