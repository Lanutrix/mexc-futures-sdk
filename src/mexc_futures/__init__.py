"""MEXC Futures SDK - Python client for MEXC Futures API.

This SDK provides both async and sync clients for interacting with
the MEXC Futures REST API and WebSocket streams.

Example (async):
    ```python
    import asyncio
    from mexc_futures import MexcFuturesClient, SDKConfig

    async def main():
        config = SDKConfig(auth_token="WEB...")
        async with MexcFuturesClient(config) as client:
            ticker = await client.get_ticker("BTC_USDT")
            print(f"BTC price: {ticker.data.lastPrice}")

    asyncio.run(main())
    ```

Example (sync):
    ```python
    from mexc_futures import MexcFuturesClientSync, SDKConfig

    config = SDKConfig(auth_token="WEB...")
    with MexcFuturesClientSync(config) as client:
        ticker = client.get_ticker("BTC_USDT")
        print(f"BTC price: {ticker.data.lastPrice}")
    ```
"""

__version__ = "0.1.0"

# Main clients
from .client import MexcFuturesClient, MexcFuturesClientSync
from .websocket import MexcFuturesWebSocket, FilterType

# Configuration
from .utils import SDKConfig, WebSocketConfig, get_logger

# Exceptions
from .exceptions import (
    MexcFuturesError,
    MexcApiError,
    MexcAuthenticationError,
    MexcNetworkError,
    MexcRateLimitError,
    MexcSignatureError,
    MexcValidationError,
    MexcWebSocketError,
    format_error_for_logging,
    parse_httpx_error,
)

# Constants
from .constants import (
    API_BASE_URL,
    WEBSOCKET_URL,
    DEFAULT_HEADERS,
    get_default_headers,
    Endpoints,
    WsChannels,
    KLINE_INTERVALS,
)

# Models - Orders
from .models import (
    OrderSide,
    OrderType,
    OpenType,
    OrderCategory,
    OrderState,
    OrderHistoryParams,
    Order,
    OrderHistoryResponse,
    OrderDealsParams,
    OrderDeal,
    OrderDealsResponse,
    CancelOrderResult,
    CancelOrderResponse,
    CancelOrderByExternalIdRequest,
    CancelOrderByExternalIdResponse,
    CancelAllOrdersRequest,
    CancelAllOrdersResponse,
    SubmitOrderRequest,
    SubmitOrderResponse,
    GetOrderData,
    GetOrderResponse,
)

# Models - Account
from .models import (
    RiskLimit,
    FeeRate,
    AccountResponse,
    AccountAsset,
    AccountAssetResponse,
    PositionType,
    PositionState,
    Position,
    OpenPositionsResponse,
    PositionHistoryParams,
    PositionHistoryResponse,
)

# Models - Market
from .models import (
    RiseFallRates,
    TickerData,
    TickerResponse,
    ContractDetail,
    ContractDetailResponse,
    DepthEntry,
    ContractDepthData,
    ContractDepthResponse,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "MexcFuturesClient",
    "MexcFuturesClientSync",
    "MexcFuturesWebSocket",
    "FilterType",
    # Configuration
    "SDKConfig",
    "WebSocketConfig",
    "get_logger",
    # Exceptions
    "MexcFuturesError",
    "MexcApiError",
    "MexcAuthenticationError",
    "MexcNetworkError",
    "MexcRateLimitError",
    "MexcSignatureError",
    "MexcValidationError",
    "MexcWebSocketError",
    "format_error_for_logging",
    "parse_httpx_error",
    # Constants
    "API_BASE_URL",
    "WEBSOCKET_URL",
    "DEFAULT_HEADERS",
    "get_default_headers",
    "Endpoints",
    "WsChannels",
    "KLINE_INTERVALS",
    # Order models
    "OrderSide",
    "OrderType",
    "OpenType",
    "OrderCategory",
    "OrderState",
    "OrderHistoryParams",
    "Order",
    "OrderHistoryResponse",
    "OrderDealsParams",
    "OrderDeal",
    "OrderDealsResponse",
    "CancelOrderResult",
    "CancelOrderResponse",
    "CancelOrderByExternalIdRequest",
    "CancelOrderByExternalIdResponse",
    "CancelAllOrdersRequest",
    "CancelAllOrdersResponse",
    "SubmitOrderRequest",
    "SubmitOrderResponse",
    "GetOrderData",
    "GetOrderResponse",
    # Account models
    "RiskLimit",
    "FeeRate",
    "AccountResponse",
    "AccountAsset",
    "AccountAssetResponse",
    "PositionType",
    "PositionState",
    "Position",
    "OpenPositionsResponse",
    "PositionHistoryParams",
    "PositionHistoryResponse",
    # Market models
    "RiseFallRates",
    "TickerData",
    "TickerResponse",
    "ContractDetail",
    "ContractDetailResponse",
    "DepthEntry",
    "ContractDepthData",
    "ContractDepthResponse",
]

