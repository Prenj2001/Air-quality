from playwright.sync_api import sync_playwright
import pandas as pd
import os

def run():
    with sync_playwright() as p:
        # 1. Launch a headless browser (invisible to the user)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 2. Go to the URL
        url = "https://rhmzrs.com/kontrola-kvaliteta-vazduha"
        print(f"Loading {url}...")
        page.goto(url)

        # 3. Wait for the specific data table to load
        # We look for a table header that contains "PM10" to ensure we get the right table
        try:
            page.wait_for_selector("table:has-text('PM10')", timeout=15000)
        except:
            print("Timeout: Table not found. The page might be loading too slowly.")
            browser.close()
            return

        # 4. Extract the HTML of the "Current Data" table
        # There are two tables; usually the first one with data is the one we want.
        # This locator finds the table that definitely contains "Station" (Станица) and "PM10"
        table_html = page.locator("table", has_text="PM10").first.inner_html()

        # 5. Parse it with Pandas
        # We wrap it in <table> tags so pandas recognizes it
        dfs = pd.read_html(f"<table>{table_html}</table>")
        
        if dfs:
            df = dfs[0]
            
            # Optional: Clean up the data (remove empty columns if any)
            df = df.dropna(how='all', axis=1)
            
            # 6. Save to CSV
            # We append the timestamp to the filename or just overwrite 'latest_data.csv'
            output_file = "air_quality_data.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig') 
            print(f"Success! Scraped {len(df)} rows to {output_file}")
            print(df.head()) # Print first few rows to logs for verification
        else:
            print("No tables found in the HTML.")

        browser.close()

if __name__ == "__main__":
    run()
