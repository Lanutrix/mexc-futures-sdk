"""Constants for MEXC Futures SDK."""

import re

from fake_useragent import UserAgent

API_BASE_URL = "https://futures.mexc.com/api/v1"

WEBSOCKET_URL = "wss://contract.mexc.com/edge"

# User agent generator
_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def _parse_ua_for_sec_ch(user_agent: str) -> tuple[str, str]:
    """Parse user-agent to generate sec-ch-ua and sec-ch-ua-platform.

    Args:
        user_agent: Full user-agent string

    Returns:
        Tuple of (sec_ch_ua, sec_ch_ua_platform)
    """
    # Detect platform
    if "Windows" in user_agent:
        platform = '"Windows"'
    elif "Macintosh" in user_agent or "Mac OS" in user_agent:
        platform = '"macOS"'
    else:
        platform = '"Windows"'

    # Extract Chrome/Edge version
    chrome_match = re.search(r"Chrome/(\d+)", user_agent)
    edge_match = re.search(r"Edg/(\d+)", user_agent)

    if edge_match:
        version = edge_match.group(1)
        sec_ch_ua = f'"Microsoft Edge";v="{version}", "Chromium";v="{version}", "Not.A/Brand";v="99"'
    elif chrome_match:
        version = chrome_match.group(1)
        sec_ch_ua = f'"Chromium";v="{version}", "Google Chrome";v="{version}", "Not.A/Brand";v="99"'
    else:
        # Fallback
        sec_ch_ua = '"Chromium";v="130", "Google Chrome";v="130", "Not.A/Brand";v="99"'

    return sec_ch_ua, platform


class Endpoints:
    """API endpoint paths."""

    # Private endpoints (require authentication)
    SUBMIT_ORDER = "/private/order/submit"
    CANCEL_ORDER = "/private/order/cancel"
    CANCEL_ORDER_BY_EXTERNAL_ID = "/private/order/cancel_with_external"
    CANCEL_ALL_ORDERS = "/private/order/cancel_all"
    ORDER_HISTORY = "/private/order/list/history_orders"
    ORDER_DEALS = "/private/order/list/order_deals"
    GET_ORDER = "/private/order/get"  # GET /private/order/get/{order_id}
    GET_ORDER_BY_EXTERNAL_ID = "/private/order/external"  # GET /private/order/external/{symbol}/{external_oid}
    RISK_LIMIT = "/private/account/risk_limit"
    FEE_RATE = "/private/account/contract/fee_rate"
    ACCOUNT_ASSET = "/private/account/asset"
    OPEN_POSITIONS = "/private/position/open_positions"
    POSITION_HISTORY = "/private/position/list/history_positions"

    # Public endpoints (no authentication required)
    TICKER = "/contract/ticker"
    CONTRACT_DETAIL = "/contract/detail"
    CONTRACT_DEPTH = "/contract/depth"


def get_default_headers() -> dict[str, str]:
    """Generate default browser headers with random user-agent and matching sec-ch-ua."""
    user_agent = _ua.random
    sec_ch_ua, sec_ch_ua_platform = _parse_ua_for_sec_ch(user_agent)

    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "language": "English",
        "origin": "https://www.mexc.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.mexc.com/",
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": sec_ch_ua_platform,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": user_agent,
        "x-language": "en-US",
    }


# Default headers (for backwards compatibility, generates new UA each access)
DEFAULT_HEADERS = get_default_headers()


# WebSocket channel names
class WsChannels:
    """WebSocket channel names for subscription."""

    # Public channels
    TICKERS = "push.tickers"
    TICKER = "push.ticker"
    DEAL = "push.deal"
    DEPTH = "push.depth"
    KLINE = "push.kline"
    FUNDING_RATE = "push.funding.rate"
    INDEX_PRICE = "push.index.price"
    FAIR_PRICE = "push.fair.price"

    # Private channels
    ORDER = "push.personal.order"
    ORDER_DEAL = "push.personal.order.deal"
    POSITION = "push.personal.position"
    ASSET = "push.personal.asset"
    STOP_ORDER = "push.personal.stop.order"
    STOP_PLAN_ORDER = "push.personal.stop.planorder"
    LIQUIDATE_RISK = "push.personal.liquidate.risk"
    ADL_LEVEL = "push.personal.adl.level"
    RISK_LIMIT = "push.personal.risk.limit"
    PLAN_ORDER = "push.personal.plan.order"


# K-Line intervals
KLINE_INTERVALS = (
    "Min1",
    "Min5",
    "Min15",
    "Min30",
    "Min60",
    "Hour4",
    "Hour8",
    "Day1",
    "Week1",
    "Month1",
)

