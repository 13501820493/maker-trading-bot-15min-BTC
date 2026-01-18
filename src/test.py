# Choose based on your wallet type (see table above)
import re

from datetime import datetime
import httpx
from dotenv import load_dotenv
from py_clob_client import ClobClient, OrderArgs, OrderType
import os
import logging
from py_clob_client.order_builder.constants import BUY
from src.lookup import fetch_market_from_slug
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()
private_key = os.getenv("POLYMARKET_PRIVATE_KEY")
api_key = os.getenv("POLYMARKET_API_KEY")
api_secret = os.getenv("POLYMARKET_API_SECRET")
api_passphrase = os.getenv("POLYMARKET_API_PASSPHRASE")
signature_type = int(os.getenv("POLYMARKET_SIGNATURE_TYPE", "1"))
funder = os.getenv("POLYMARKET_FUNDER", "")

logger = logging.getLogger(__name__)

def runmaker():
    client = init_instance()
    """使用 APScheduler，功能最强大"""
    scheduler = BlockingScheduler()
    scheduler.add_job(your_task, 'interval', minutes=15, kwargs={'client': client},next_run_time=datetime.now())
    scheduler.start()

def find_current_btc_15min_market() -> str:
    """
    Find the current active BTC 15min market on Polymarket.

    Searches for markets matching the pattern 'btc-updown-15m-<timestamp>'
    and returns the slug of the most recent/active market.
    """

    try:
        # Search on Polymarket's crypto 15min page
        page_url = "https://polymarket.com/crypto/15M"
        resp = httpx.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()

        # Find the BTC market slug in the HTML
        pattern = r'eth-updown-15m-(\d+)'
        matches = re.findall(pattern, resp.text)

        if not matches:
            raise RuntimeError("No active BTC 15min market found")

        # Prefer the most recent timestamp that is still OPEN.
        # 15min markets close 900s after the timestamp in the slug.
        now_ts = int(datetime.now().timestamp())
        all_ts = sorted((int(ts) for ts in matches), reverse=True)
        open_ts = [ts for ts in all_ts if now_ts < (ts + 900)]
        chosen_ts = open_ts[0] if open_ts else all_ts[0]
        slug = f"btc-updown-15m-{chosen_ts}"

        logger.info(f"✅ Market found: {slug}")
        return slug

    except Exception as e:
        logger.error(f"Error searching for BTC 15min market: {e}")
        # Fallback: try with the last known one
        logger.warning("Using default market from configuration...")

def get_time_remaining(market_end_timestamp):
    """Get remaining time until market closes."""
    if not market_end_timestamp:
        return "Unknown"

    now = int(datetime.now().timestamp())
    remaining = market_end_timestamp - now

    if remaining <= 0:
        return "CLOSED"
    return None

def init_instance():
    host = "https://clob.polymarket.com"
    chain_id = 137  # Polygon mainnet
    client = ClobClient(host, key=private_key, chain_id=chain_id, signature_type=signature_type, funder=funder or None)

    user_api_creds = client.create_or_derive_api_creds()
    print(user_api_creds.api_key)
    print(user_api_creds.api_secret)
    print(user_api_creds.api_passphrase)
    print("\n2. Deriving API credentials from private key...")
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)
    print(f"   ✓ API Key: {creds.api_key}")
    print(f"   ✓ Credentials configured")
    return client

def your_task(client):
    print(datetime.now().strftime('%H:%M:%S'))
    current_slug = find_current_btc_15min_market()
    print(current_slug)

    market_info = fetch_market_from_slug(current_slug)
    print(market_info["yes_token_id"])
    print(market_info["no_token_id"])

    res = client.create_and_post_order(
        OrderArgs(
            token_id=market_info["yes_token_id"],
            price=0.03,  # Price per share ($0.50)
            size=33,  # Number of shares
            side=BUY,  # BUY or SELL
        )  # Good-Til-Cancelled
    )
    print(res["status"])
    res = client.create_and_post_order(
        OrderArgs(
            token_id=market_info["no_token_id"],
            price=0.03,  # Price per share ($0.50)
            size=33,  # Number of shares
            side=BUY,  # BUY or SELL
        )  # Good-Til-Cancelled
    )
    print(res["status"])


if __name__ == '__main__':

    runmaker()