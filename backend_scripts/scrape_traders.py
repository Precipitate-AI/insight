# backend_scripts/scrape_traders.py
import os
import json
import requests
from bs4 import BeautifulSoup
import datetime

# --- Configuration ---
HYPERDASH_TOP_TRADERS_URL = "https://hyperdash.info/top-traders"
# How many traders to attempt to scrape from Hyperdash (max 100 on page)
NUMBER_OF_TOP_TRADERS_TO_FETCH = 100 # You can adjust this

# --- Output Configuration ---
# Where to save the trader list. This file will be read by the report generation script.
# Assuming backend_scripts is at project_root/backend_scripts
# We'll save it within backend_scripts for the other script to easily access.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR_RELATIVE_TO_SCRIPT = "." # Save in current (backend_scripts) directory
TRADER_LIST_FILENAME = "trader_list.json"
OUTPUT_FILEPATH = os.path.abspath(os.path.join(SCRIPT_DIR, OUTPUT_DIR_RELATIVE_TO_SCRIPT, TRADER_LIST_FILENAME))

def ensure_output_dir_exists():
    target_dir = os.path.dirname(OUTPUT_FILEPATH)
    if not os.path.exists(target_dir): # Should always be true for "." but good practice
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")

def save_trader_list(addresses):
    ensure_output_dir_exists()
    data_to_save = {
        "last_scraped_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "source_url": HYPERDASH_TOP_TRADERS_URL,
        "trader_addresses": addresses
    }
    with open(OUTPUT_FILEPATH, "w") as f:
        json.dump(data_to_save, f, indent=2)
    print(f"Saved {len(addresses)} trader addresses to {OUTPUT_FILEPATH}")

def scrape_and_save_top_trader_addresses():
    print(f"Attempting to scrape top trader addresses from {HYPERDASH_TOP_TRADERS_URL}...")
    addresses = []
    
    # Define a common browser User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        # You can try other User-Agents:
        # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'
    }

    try:
        # Add the headers to your request
        print(f"DEBUG: Making GET request to {HYPERDASH_TOP_TRADERS_URL} with headers...")
        response = requests.get(HYPERDASH_TOP_TRADERS_URL, headers=headers, timeout=20) # Increased timeout slightly
        
        print(f"DEBUG: Response status code: {response.status_code}")
        response.raise_for_status()  # This will raise an exception if status is 4xx or 5xx

        soup = BeautifulSoup(response.content, 'html.parser')
        print(f"DEBUG: Successfully parsed HTML content. Page title: {soup.title.string if soup.title else 'No title found'}")
        
        # --- HTML Parsing Logic ---
        # You MUST inspect the live Hyperdash page to identify correct selectors.
        # The selectors below are educated GUESSES based on common patterns.
        
        # Example: Try to find a table that might contain the traders
        # This is highly speculative and needs to be verified by inspecting the actual page
        # trader_table = soup.find('table') # Or a more specific table class/id
        # if trader_table:
        #     print("DEBUG: Found a <table> element.")
        #     user_rows = trader_table.find_all('tr') # Find rows in the table
        # else:
        #     print("DEBUG: Did not find a generic <table>. Falling back to searching all <a> tags.")
        #     user_rows = [] # Placeholder if table not found, forcing fallback below

        # Broad search for <a> tags if specific table/row search fails or is not implemented
        # This was the previous approach.
        user_links = soup.find_all('a', href=True)
        print(f"DEBUG: Found {len(user_links)} total <a> tags on the page.")
        
        found_count = 0
        # Iterate through identified elements (rows or general links)
        # If using user_rows from a table: for row in user_rows: links_in_row = row.find_all('a', href=True) ...
        for link_idx, link in enumerate(user_links): # Using the general link search for now
            href = link.get('href', '') # Use .get() for safety
            # print(f"DEBUG LINK {link_idx}: {href}") # Very verbose, uncomment if really stuck

            # Hyperdash structure: links like '/leaderboard/user/0x...' or '/user/0x...'
            if href.startswith('/leaderboard/user/') or href.startswith('/user/'):
                # print(f"DEBUG: Potential user link found: {href}")
                try:
                    # Extract the address part, e.g., from "/user/0x123abc..."
                    address_part = href.split('/')[-1]
                    # Basic address validation (starts with 0x, 42 chars long)
                    if address_part.startswith("0x") and len(address_part) == 42:
                        if address_part not in addresses: # Avoid duplicates
                             addresses.append(address_part)
                             found_count +=1
                             print(f"DEBUG: Added address: {address_part} (Count: {found_count})")
                             if found_count >= NUMBER_OF_TOP_TRADERS_TO_FETCH:
                                 print(f"DEBUG: Reached NUMBER_OF_TOP_TRADERS_TO_FETCH limit ({NUMBER_OF_TOP_TRADERS_TO_FETCH}).")
                                 break
                except IndexError:
                    # This might happen if split('/')[-1] fails on an unexpected href format
                    print(f"DEBUG: IndexError processing link: {href}")
                    continue
            
            if found_count >= NUMBER_OF_TOP_TRADERS_TO_FETCH: # Break outer loop too
                break
        
        if addresses:
            print(f"Successfully identified {len(addresses)} potential trader addresses from HTML.")
            save_trader_list(addresses)
        else:
            print("Could not identify trader addresses with the current parsing logic.")
            print("This could be due to: ")
            print("  1. Incorrect BeautifulSoup selectors (most likely).")
            print("  2. The page structure has changed significantly.")
            print("  3. The required content is loaded by JavaScript (requests/BS4 won't see it).")
            print("Please re-inspect the HTML of hyperdash.info/top-traders and update the parsing logic.")
            print(f"No trader list was saved to {OUTPUT_FILEPATH}.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Status: {response.status_code if 'response' in locals() else 'N/A'}")
        if 'response' in locals() and response.status_code == 403:
            print("A 403 Forbidden error means the server is blocking us. User-Agent might not be enough.")
            print("Further anti-scraping measures might be in place (e.g., Cloudflare, JS challenges).")
        # print(f"DEBUG: Page content received on error (first 500 chars):\n{response.text[:500] if 'response' in locals() else 'No response content'}")

    except requests.RequestException as e:
        # For other network issues like DNS failure, Connection timeout etc.
        print(f"Error during requests to {HYPERDASH_TOP_TRADERS_URL}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors
    
    return addresses

if __name__ == "__main__":
    print("--- Starting Top Trader Scraper ---")
    print(f"DEBUG: Will save trader list to: {OUTPUT_FILEPATH}")
    
    scraped_addresses_result = scrape_and_save_top_trader_addresses()
    
    if scraped_addresses_result: # Check if the list is not None and not empty
        print(f"--- Scraper Finished --- Found {len(scraped_addresses_result)} addresses.")
    elif scraped_addresses_result == []: # Explicitly check for empty list if no error occurred
        print("--- Scraper Finished --- Found 0 addresses matching criteria.")
    else: # Implies an error might have occurred preventing list population
        print("--- Scraper Finished --- Scraper may have encountered an error or found no addresses.")

