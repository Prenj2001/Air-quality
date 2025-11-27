import requests
import sys
import json # Import json for better printing

# The API endpoint identified from the network traffic
API_ENDPOINT = "https://rhmzrs.com/data/feeds/EkoPodaci.json"

def run():
    print(f"Attempting to fetch data directly from API: {API_ENDPOINT}")
    
    try:
        # 1. Fetch data directly via HTTP request
        response = requests.get(API_ENDPOINT, timeout=30)
        response.raise_for_status() 
        
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ FATAL ERROR: Direct API call failed (Network/Timeout issue). Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\n❌ FATAL ERROR: Response was not valid JSON.")
        print(f"Response text start: {response.text[:500]}...")
        sys.exit(1)

    print("\n--- JSON STRUCTURE DEBUG LOG ---")
    
    # Print the type and the first part of the dictionary/list to see the keys
    print(f"Data Type: {type(data)}")
    
    # Use json.dumps to print the structure cleanly
    json_string = json.dumps(data, indent=2, ensure_ascii=False)
    
    # Print only the first 50 lines or 1500 characters to keep the log manageable
    print(json_string[:1500])
    
    if len(json_string) > 1500:
        print("\n... (Truncated. Structure should be visible above) ...")

    print("----------------------------------")
    
    print("\n❌ FATAL ERROR: Script stopped for manual inspection of JSON structure.")
    sys.exit(1)

if __name__ == "__main__":
    run()
