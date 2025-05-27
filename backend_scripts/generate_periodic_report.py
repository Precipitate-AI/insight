# backend_scripts/generate_periodic_report.py

import os
import json
import datetime
import time
from dotenv import load_dotenv

from hyperliquid.info import Info
from hyperliquid.utils import constants

from openai import OpenAI # For OpenRouter

# --- Configuration ---
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
GEMINI_MODEL_NAME = "google/gemini-1.5-flash-latest" # Or "google/gemini-1.5-pro-latest"

# --- Hyperliquid Config ---
# How many of the loaded traders to actually get detailed data for (can be less than total in file)
NUMBER_OF_TRADERS_TO_PROCESS_FROM_LIST = 10 # Adjust as needed
NUMBER_OF_RECENT_FILLS_PER_TRADER = 5
TICKERS_TO_MONITOR = ["BTC", "ETH", "SOL", "PEPE", "DOGE"] # Adjust as needed

# --- Input/Output Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Input trader list
TRADER_LIST_FILENAME = "trader_list.json"
TRADER_LIST_FILEPATH = os.path.join(SCRIPT_DIR, TRADER_LIST_FILENAME)

# Output for Next.js frontend
OUTPUT_DIR_NEXTJS_RELATIVE = "../public/data" # Relative to this script's location
OUTPUT_DIR_NEXTJS_ABSOLUTE = os.path.abspath(os.path.join(SCRIPT_DIR, OUTPUT_DIR_NEXTJS_RELATIVE))

# --- Helper Functions ---
def ensure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

def save_json_to_nextjs_public(data, filename):
    ensure_dir_exists(OUTPUT_DIR_NEXTJS_ABSOLUTE)
    filepath = os.path.join(OUTPUT_DIR_NEXTJS_ABSOLUTE, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved data for Next.js at: {filepath}")

def load_trader_list():
    print(f"Loading trader list from: {TRADER_LIST_FILEPATH}")
    if not os.path.exists(TRADER_LIST_FILEPATH):
        print(f"ERROR: Trader list file not found at {TRADER_LIST_FILEPATH}. Please run scrape_traders.py first.")
        return []
    try:
        with open(TRADER_LIST_FILEPATH, "r") as f:
            data = json.load(f)
            addresses = data.get("trader_addresses", [])
            print(f"Loaded {len(addresses)} traders from the list.")
            return addresses
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {TRADER_LIST_FILEPATH}. File might be corrupted.")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred loading trader list: {e}")
        return []

# --- Hyperliquid Data Fetching Functions (Mostly same as before) ---
def get_hyperliquid_market_data(hl_info_client, asset_metas):
    # (This function remains the same as in the previous combined script)
    # ... (copy from previous generate_report.py)
    print("Fetching general market data (OI, Funding, Prices)...")
    market_summary_data = {}
    try:
        meta_and_ctxs_data = hl_info_client.meta_and_asset_ctxs()
        all_mids = hl_info_client.all_mids()

        for asset_ctx in meta_and_ctxs_data.get('assetCtxs', []):
            coin = asset_ctx.get('name')
            if coin in TICKERS_TO_MONITOR and coin in all_mids:
                market_summary_data[coin] = {
                    "name": coin,
                    "price": float(all_mids[coin]) if all_mids[coin] else 0.0,
                    "open_interest_usd": float(asset_ctx.get('openInterest', 0)),
                    "funding_rate_hourly": float(asset_ctx.get('funding', 0)) * 100,
                    "max_leverage": asset_metas.get(coin, {}).get('maxLeverage', 10),
                    "volume_24h_usd": float(asset_ctx.get('dayNtlV', [0.0])[0])
                }
        print(f"Fetched market data for {len(market_summary_data)} monitored tickers.")
    except Exception as e:
        print(f"Error fetching general market data: {e}")
    return market_summary_data

def get_detailed_trader_data(hl_info_client, trader_address):
    # (This function remains the same as in the previous combined script)
    # ... (copy from previous generate_report.py)
    print(f"Fetching detailed data for trader: {trader_address}")
    trader_snapshot = {
        "address": trader_address,
        "open_positions": [],
        "recent_fills": [],
        "total_unrealized_pnl": 0.0,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    try:
        user_state = hl_info_client.user_state(trader_address)
        user_fills_raw = hl_info_client.user_fills(trader_address)

        current_unrealized_pnl_sum = 0.0
        if user_state and 'assetPositions' in user_state:
            for asset_pos in user_state['assetPositions']:
                if asset_pos and float(asset_pos['position']['szi']) != 0:
                    coin = asset_pos['position']['coin']
                    entry_px = float(asset_pos['position']['entryPx']) if asset_pos['position']['entryPx'] else 0.0
                    szi = float(asset_pos['position']['szi'])
                    unrealized_pnl = float(asset_pos['position']['unrealizedPnl']) if asset_pos['position']['unrealizedPnl'] else 0.0
                    leverage_info = asset_pos['position'].get('leverage', {})
                    leverage_val = float(leverage_info.get('value', 0))
                    leverage = leverage_val

                    side = "LONG" if szi > 0 else "SHORT"
                    position_value_usd = abs(szi * entry_px)

                    trader_snapshot["open_positions"].append({
                        "coin": coin,
                        "side": side,
                        "size_tokens": abs(szi),
                        "position_value_usd": position_value_usd,
                        "entry_price": entry_px,
                        "unrealized_pnl_usd": unrealized_pnl,
                        "leverage": leverage,
                    })
                    current_unrealized_pnl_sum += unrealized_pnl
        trader_snapshot["total_unrealized_pnl"] = current_unrealized_pnl_sum

        if user_fills_raw:
            for fill in user_fills_raw[:NUMBER_OF_RECENT_FILLS_PER_TRADER]:
                trader_snapshot["recent_fills"].append({
                    "coin": fill['coin'],
                    "side": fill['side'].upper(),
                    "size_tokens": float(fill['sz']),
                    "price": float(fill['px']),
                    "value_usd": float(fill['sz']) * float(fill['px']),
                    "time": datetime.datetime.fromtimestamp(fill['time'] // 1000).strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "is_liquidation": fill.get('liquidationMarkPx') is not None,
                })
        print(f"Successfully processed data for {trader_address}. Open Positions: {len(trader_snapshot['open_positions'])}, Recent Fills: {len(trader_snapshot['recent_fills'])}")
    except Exception as e:
        print(f"Error fetching data for trader {trader_address}: {e}")
        trader_snapshot["error"] = str(e)
    return trader_snapshot


# --- AI Summarization Function (Same as before) ---
def get_ai_summary(market_data_str, top_traders_data_str):
    # (This function remains the same as in the previous combined script)
    # ... (copy from previous generate_report.py)
    if not OPENROUTER_API_KEY:
        print("OpenRouter API key not found. Skipping AI summary.")
        return "AI Summary generation skipped: API key missing."

    client = OpenAI(
        base_url=OPENROUTER_API_BASE,
        api_key=OPENROUTER_API_KEY,
    )

    system_prompt = """
    You are an expert crypto trading analyst AI for "Insight", a Hyperliquid analytics dashboard.
    Your task is to provide a concise, insightful, and data-driven summary of recent trading activity
    on Hyperliquid based on the provided snapshot. Format your output in Markdown.

    Key areas to cover:
    1.  **Overall Market Sentiment:** Briefly touch upon if the general sentiment from the data looks bullish, bearish, or mixed for the monitored tickers.
    2.  **Key Ticker Analysis:** For each major ticker (BTC, ETH, SOL, etc.), highlight notable changes in price, Open Interest, and Funding Rates. Mention any significant 24h volume.
    3.  **Top Trader Activity:** For the summarized top traders:
        *   Identify any very large new positions or closed positions.
        *   Comment on common themes: Are many top traders aligned on a particular asset or direction?
        *   Note any high leverage plays or significant P&L.
    4.  **Actionable Insights/Observations (Optional & Cautious):** If any clear patterns or potential short-term implications emerge, mention them cautiously. Avoid giving direct financial advice.

    Structure:
    ## Insight Report: Hyperliquid Activity Snapshot ({current_time})

    ###  시장 동향 (Market Overview)
    - **General Sentiment:** ...
    - **BTC:** Price: $X, OI: $Ym, Funding: Z%, Volume: $Vm. Observations: ...
    - **ETH:** Price: $X, OI: $Ym, Funding: Z%, Volume: $Vm. Observations: ...
    - (Repeat for other key tickers)

    ### 주요 트레이더 활동 (Top Trader Activity)
    - Trader `0xabc...xyz`:
        - Notable Open Positions: [Coin SIDE @ $Price, Size $X, PNL $Y, Leverage Zx]
        - Recent Closed Positions: [Coin SIDE Profit/Loss of $Z] (If P&L available, otherwise just fill)
        - Brief analysis of their current stance if discernible.
    - (Repeat for other summarized traders)

    ### 요약 및 관찰 (Summary & Observations)
    - Concluding thoughts on current market dynamics on Hyperliquid based *only* on the provided data.

    Be professional, use financial terminology correctly, and keep it concise. Focus on what changed or is notable.
    Use Korean for section headers as specified, but the main content body in English.
    Current UTC Time for report context: {current_time_utc}
    """

    prompt_content = f"""
    Here is the latest data snapshot from Hyperliquid:

    ## Market Data Snapshot:
    {market_data_str}

    ## Top Traders Snapshot:
    {top_traders_data_str}

    Please generate the report based on this data and the system prompt instructions.
    """

    full_system_prompt = system_prompt.format(
        current_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
        current_time_utc=datetime.datetime.utcnow().isoformat() + "Z"
    )

    print("\nSending data to Gemini for summarization...")
    try:
        completion = client.chat.completions.create(
            model=GEMINI_MODEL_NAME,
            messages=[
                {"role": "system", "content": full_system_point}, # Corrected typo: full_system_prompt
                {"role": "user", "content": prompt_content},
            ],
            temperature=0.6,
            max_tokens=2000
        )
        summary = completion.choices[0].message.content
        print("AI Summary received.")
        return summary
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"Error during AI summarization: {e}\n\n[Data provided to LLM was omitted for brevity in this error message]"


# --- Main Orchestration Logic ---
def main_periodic_report():
    print_stars_line("Starting Periodic Hyperliquid Insight Report Generation")
    start_time = time.time()

    ensure_dir_exists(OUTPUT_DIR_NEXTJS_ABSOLUTE) # For Next.js frontend files

    # 1. Load Trader Addresses
    print_stars_line("Step 1: Loading Trader Addresses from File")
    all_loaded_addresses = load_trader_list()
    if not all_loaded_addresses:
        print("No trader addresses loaded. Report will not include detailed trader activity.")
        addresses_to_process = []
    else:
        addresses_to_process = all_loaded_addresses[:NUMBER_OF_TRADERS_TO_PROCESS_FROM_LIST]
        print(f"Will process detailed data for up to {len(addresses_to_process)} traders from the list.")

    # 2. Initialize Hyperliquid Info Client
    try:
        hl_info_client = Info(constants.MAINNET_API_URL, skip_ws=True)
        all_hl_meta = hl_info_client.meta()
        asset_metas = {asset_info['name']: asset_info for asset_info in all_hl_meta['universe']}
    except Exception as e:
        print(f"CRITICAL ERROR: Could not initialize Hyperliquid Info client or fetch metadata: {e}")
        error_report_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z", "status": "ERROR",
            "message": "Failed to initialize Hyperliquid SDK or fetch initial metadata.", "error_details": str(e)
        }
        save_json_to_nextjs_public(error_report_data, "error_report.json")
        return

    # 3. Fetch General Market Data
    print_stars_line("Step 2: Fetching General Market Data for Monitored Tickers")
    market_data_snapshot = get_hyperliquid_market_data(hl_info_client, asset_metas)
    save_json_to_nextjs_public(market_data_snapshot, "market_snapshot.json")

    # 4. Fetch Detailed Data for Top Traders from the loaded list
    print_stars_line(f"Step 3: Fetching Detailed Data for {len(addresses_to_process)} Traders")
    processed_traders_data = []
    if addresses_to_process:
        for addr in addresses_to_process:
            trader_data = get_detailed_trader_data(hl_info_client, addr)
            processed_traders_data.append(trader_data)
            time.sleep(0.2)
    else:
        print("No trader addresses to process. Skipping detailed trader data fetching.")
    save_json_to_nextjs_public(processed_traders_data, "top_traders_snapshot.json")

    # 5. Prepare Data Strings for LLM
    # (This part remains the same as in the previous combined script)
    # ... (copy from previous generate_report.py)
    print_stars_line("Step 4: Preparing Data for AI Summarization")
    market_data_llm_str = json.dumps(market_data_snapshot, indent=2) if market_data_snapshot else "No market data available."
    traders_data_llm_str_list = []
    for trader in processed_traders_data:
        trader_str = f"Trader: {trader['address']} (Total Unrealized PNL: ${trader['total_unrealized_pnl']:.2f})\n"
        trader_str += "  Open Positions:\n"
        if trader['open_positions']:
            for pos in trader['open_positions']:
                trader_str+= f"    - {pos['coin']} {pos['side']}, Size: {pos['size_tokens']:.2f} ({pos['coin']}), Entry: ${pos['entry_price']:.4f}, UPNL: ${pos['unrealized_pnl_usd']:.2f}, Lev: {pos['leverage']:.1f}x\n"
        else:
            trader_str += "    - None\n"
        trader_str += "  Recent Fills:\n"
        if trader['recent_fills']:
            for fill in trader['recent_fills']:
                trader_str += f"    - {fill['time']}: {fill['side']} {fill['size_tokens']:.2f} {fill['coin']} @ ${fill['price']:.4f}\n"
        else:
            trader_str += "    - None\n"
        traders_data_llm_str_list.append(trader_str)
    top_traders_llm_str = "\n".join(traders_data_llm_str_list) if traders_data_llm_str_list else "No top trader data available to summarize."


    # 6. Get AI Summary
    print_stars_line("Step 5: Generating AI Summary")
    ai_summary_markdown = get_ai_summary(market_data_llm_str, top_traders_llm_str)
    
    ensure_dir_exists(OUTPUT_DIR_NEXTJS_ABSOLUTE)
    summary_filepath_md = os.path.join(OUTPUT_DIR_NEXTJS_ABSOLUTE, "ai_summary.md")
    with open(summary_filepath_md, "w", encoding="utf-8") as f:
        f.write(ai_summary_markdown)
    print(f"AI Summary saved to {summary_filepath_md}")

    # 7. Create a consolidated report JSON
    consolidated_report = {
        "last_updated_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "market_snapshot": market_data_snapshot,
        "top_traders_snapshot": processed_traders_data,
        "ai_summary_markdown": ai_summary_markdown,
        "generation_duration_seconds": round(time.time() - start_time, 2)
    }
    save_json_to_nextjs_public(consolidated_report, "report_summary.json")
    
    print_stars_line("Periodic Hyperliquid Insight Report Generation Complete!")
    print(f"Total execution time: {consolidated_report['generation_duration_seconds']:.2f} seconds.")

def print_stars_line(message):
    print("\n" + "*"*10 + f" {message} " + "*"*10)

if __name__ == "__main__":
    main_periodic_report()

