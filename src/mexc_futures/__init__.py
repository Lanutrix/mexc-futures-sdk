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

from .client import MexcFuturesClient, MexcFuturesClientSync
from .constants import (
    API_BASE_URL,
    DEFAULT_HEADERS,
    KLINE_INTERVALS,
    WEBSOCKET_URL,
    Endpoints,
    WsChannels,
    get_default_headers,
)
from .exceptions import (
    MexcApiError,
    MexcAuthenticationError,
    MexcFuturesError,
    MexcNetworkError,
    MexcRateLimitError,
    MexcSignatureError,
    MexcValidationError,
    MexcWebSocketError,
    format_error_for_logging,
    parse_httpx_error,
)
from .models import (
    AccountAsset,
    AccountAssetResponse,
    AccountResponse,
    CancelAllOrdersRequest,
    CancelAllOrdersResponse,
    CancelOrderByExternalIdRequest,
    CancelOrderByExternalIdResponse,
    CancelOrderResponse,
    CancelOrderResult,
    ContractDepthData,
    ContractDepthResponse,
    ContractDetail,
    ContractDetailResponse,
    DepthEntry,
    FeeRate,
    GetOrderData,
    GetOrderResponse,
    OpenPositionsResponse,
    OpenType,
    Order,
    OrderCategory,
    OrderDeal,
    OrderDealsParams,
    OrderDealsResponse,
    OrderHistoryParams,
    OrderHistoryResponse,
    OrderSide,
    OrderState,
    OrderType,
    Position,
    PositionHistoryParams,
    PositionHistoryResponse,
    PositionState,
    PositionType,
    RiseFallRates,
    RiskLimit,
    SubmitOrderRequest,
    SubmitOrderResponse,
    TickerData,
    TickerResponse,
)
from .session import SessionManager
from .utils import SDKConfig, WebSocketConfig, get_logger
from .websocket import FilterType, MexcFuturesWebSocket

__all__ = [
    # Version
    "__version__",
    # Clients
    "MexcFuturesClient",
    "MexcFuturesClientSync",
    "MexcFuturesWebSocket",
    "FilterType",
    # Session
    "SessionManager",
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

