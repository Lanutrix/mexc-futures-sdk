"""Async REST client for MEXC Futures API."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .constants import Endpoints, get_default_headers, get_random_user_agent
from .exceptions import MexcValidationError, parse_httpx_error
from .models import (
    AccountAssetResponse,
    AccountResponse,
    CancelAllOrdersRequest,
    CancelAllOrdersResponse,
    CancelOrderByExternalIdRequest,
    CancelOrderByExternalIdResponse,
    CancelOrderResponse,
    ContractDepthResponse,
    ContractDetailResponse,
    FeeRate,
    GetOrderResponse,
    OpenPositionsResponse,
    OrderDealsParams,
    OrderDealsResponse,
    OrderHistoryParams,
    OrderHistoryResponse,
    PositionHistoryParams,
    PositionHistoryResponse,
    RiskLimit,
    SubmitOrderRequest,
    SubmitOrderResponse,
    TickerResponse,
)
from .utils import SDKConfig, get_logger, mexc_crypto


class MexcFuturesClient:
    """Async client for MEXC Futures REST API.

    Uses httpx.AsyncClient for non-blocking HTTP requests.
    Supports context manager protocol for proper resource cleanup.

    Example:
        ```python
        async with MexcFuturesClient(config) as client:
            ticker = await client.get_ticker("BTC_USDT")
            print(ticker.data.lastPrice)
        ```
    """

    def __init__(self, config: SDKConfig):
        """Initialize the client.

        Args:
            config: SDK configuration with auth token and options
        """
        self.config = config
        self.logger = get_logger("mexc_futures.client", config.log_level)
        self._client: httpx.AsyncClient | None = None
        self._user_agent: str | None = None

    def _build_headers(self, include_auth: bool = True, request_body: Any = None) -> dict[str, str]:
        """Build request headers with optional authentication.

        Args:
            include_auth: Whether to include auth headers
            request_body: Request body for signature (POST requests)

        Returns:
            Dict of HTTP headers
        """
        # Use session user-agent or config override
        ua = self.config.user_agent or self._user_agent
        headers = get_default_headers(ua)

        headers.update(self.config.custom_headers)

        if include_auth:
            headers["authorization"] = self.config.auth_token

            if request_body is not None:
                signature = mexc_crypto(self.config.auth_token, request_body)
                headers["x-mxc-nonce"] = signature["time"]
                headers["x-mxc-sign"] = signature["sign"]
                self.logger.debug(f"Signature: time={signature['time']}, sign={signature['sign']}")

        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._build_headers(include_auth=False),
                cookies=self.config.custom_cookies or None,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> MexcFuturesClient:
        """Enter async context manager."""
        # Generate user-agent once per session
        if self._user_agent is None and not self.config.user_agent:
            self._user_agent = get_random_user_agent()
            self.logger.debug(f"Generated user-agent: {self._user_agent}")
        await self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        include_auth: bool = True,
    ) -> Any:
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_body: JSON body for POST requests
            include_auth: Whether to include authentication

        Returns:
            Response JSON data

        Raises:
            MexcFuturesError: On API errors
        """
        client = await self._get_client()
        if self.config.custom_cookies:
            client.cookies.update(self.config.custom_cookies)
        headers = self._build_headers(include_auth=include_auth, request_body=json_body)

        self.logger.debug(f"{method} {self.config.base_url}{endpoint}")
        if json_body:
            self.logger.debug(f"Request body: {json_body}")

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json_body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            self.logger.debug(f"Response: {response.status_code}")
            return data

        except httpx.HTTPStatusError as e:
            raise parse_httpx_error(e, endpoint, method) from e
        except httpx.RequestError as e:
            raise parse_httpx_error(e, endpoint, method) from e

    # ==================== ORDER METHODS ====================

    async def submit_order(self, order: SubmitOrderRequest) -> SubmitOrderResponse:
        """Submit a new order.

        Args:
            order: Order parameters

        Returns:
            Response with order ID on success
        """
        self.logger.info(f"Submitting order: {order.symbol} {order.side.name} {order.vol}")
        body = order.model_dump(exclude_none=True)
        data = await self._request("POST", Endpoints.SUBMIT_ORDER, json_body=body)
        return SubmitOrderResponse.model_validate(data)

    async def cancel_order(self, order_ids: list[int]) -> CancelOrderResponse:
        """Cancel orders by order IDs.

        Args:
            order_ids: List of order IDs to cancel (max 50)

        Returns:
            Response with cancellation results

        Raises:
            MexcValidationError: If order_ids is empty or exceeds 50
        """
        if not order_ids:
            raise MexcValidationError("Order IDs list cannot be empty", "order_ids")
        if len(order_ids) > 50:
            raise MexcValidationError("Cannot cancel more than 50 orders at once", "order_ids")

        data = await self._request("POST", Endpoints.CANCEL_ORDER, json_body=order_ids)
        return CancelOrderResponse.model_validate(data)

    async def cancel_order_by_external_id(
        self, request: CancelOrderByExternalIdRequest
    ) -> CancelOrderByExternalIdResponse:
        """Cancel order by external order ID.

        Args:
            request: Symbol and external order ID

        Returns:
            Cancellation response
        """
        body = request.model_dump()
        data = await self._request("POST", Endpoints.CANCEL_ORDER_BY_EXTERNAL_ID, json_body=body)
        return CancelOrderByExternalIdResponse.model_validate(data)

    async def cancel_all_orders(
        self, request: CancelAllOrdersRequest | None = None
    ) -> CancelAllOrdersResponse:
        """Cancel all orders, optionally for a specific symbol.

        Args:
            request: Optional symbol filter

        Returns:
            Cancellation response
        """
        body = request.model_dump(exclude_none=True) if request else {}
        data = await self._request("POST", Endpoints.CANCEL_ALL_ORDERS, json_body=body)
        return CancelAllOrdersResponse.model_validate(data)

    async def get_order_history(self, params: OrderHistoryParams) -> OrderHistoryResponse:
        """Get order history.

        Args:
            params: Query parameters for filtering

        Returns:
            Order history response
        """
        query = params.model_dump()
        data = await self._request("GET", Endpoints.ORDER_HISTORY, params=query)
        return OrderHistoryResponse.model_validate(data)

    async def get_order_deals(self, params: OrderDealsParams) -> OrderDealsResponse:
        """Get order deal/execution history.

        Args:
            params: Query parameters for filtering

        Returns:
            Order deals response
        """
        query = params.model_dump(exclude_none=True)
        data = await self._request("GET", Endpoints.ORDER_DEALS, params=query)
        return OrderDealsResponse.model_validate(data)

    async def get_order(self, order_id: int | str) -> GetOrderResponse:
        """Get order information by order ID.

        Args:
            order_id: Order ID to query

        Returns:
            Detailed order information
        """
        endpoint = f"{Endpoints.GET_ORDER}/{order_id}"
        data = await self._request("GET", endpoint)
        return GetOrderResponse.model_validate(data)

    async def get_order_by_external_id(self, symbol: str, external_oid: str) -> GetOrderResponse:
        """Get order information by external order ID.

        Args:
            symbol: Contract symbol (e.g., "BTC_USDT")
            external_oid: External order ID

        Returns:
            Detailed order information
        """
        endpoint = f"{Endpoints.GET_ORDER_BY_EXTERNAL_ID}/{symbol}/{external_oid}"
        data = await self._request("GET", endpoint)
        return GetOrderResponse.model_validate(data)

    # ==================== ACCOUNT METHODS ====================

    async def get_risk_limit(self) -> AccountResponse[list[RiskLimit]]:
        """Get risk limits for account.

        Returns:
            List of risk limit configurations
        """
        data = await self._request("GET", Endpoints.RISK_LIMIT)
        return AccountResponse[list[RiskLimit]].model_validate(data)

    async def get_fee_rate(self) -> AccountResponse[list[FeeRate]]:
        """Get fee rates for contracts.

        Returns:
            List of fee rate configurations
        """
        data = await self._request("GET", Endpoints.FEE_RATE)
        return AccountResponse[list[FeeRate]].model_validate(data)

    async def get_account_asset(self, currency: str) -> AccountAssetResponse:
        """Get user's single currency asset information.

        Args:
            currency: Currency symbol (e.g., "USDT", "BTC")

        Returns:
            Account asset information
        """
        endpoint = f"{Endpoints.ACCOUNT_ASSET}/{currency}"
        data = await self._request("GET", endpoint)
        return AccountAssetResponse.model_validate(data)

    async def get_open_positions(self, symbol: str | None = None) -> OpenPositionsResponse:
        """Get user's current holding positions.

        Args:
            symbol: Optional contract symbol to filter

        Returns:
            List of open positions
        """
        params = {"symbol": symbol} if symbol else None
        data = await self._request("GET", Endpoints.OPEN_POSITIONS, params=params)
        return OpenPositionsResponse.model_validate(data)

    async def get_position_history(self, params: PositionHistoryParams) -> PositionHistoryResponse:
        """Get user's position history.

        Args:
            params: Query parameters for filtering

        Returns:
            Position history response
        """
        query = params.model_dump(exclude_none=True)
        data = await self._request("GET", Endpoints.POSITION_HISTORY, params=query)
        return PositionHistoryResponse.model_validate(data)

    # ==================== MARKET METHODS ====================

    async def get_ticker(self, symbol: str) -> TickerResponse:
        """Get ticker data for a specific symbol.

        Args:
            symbol: Contract symbol (e.g., "BTC_USDT")

        Returns:
            Ticker data with prices and volumes
        """
        data = await self._request(
            "GET", Endpoints.TICKER, params={"symbol": symbol}, include_auth=False
        )
        return TickerResponse.model_validate(data)

    async def get_contract_detail(self, symbol: str | None = None) -> ContractDetailResponse:
        """Get contract information.

        Args:
            symbol: Optional contract symbol. If not provided, returns all contracts.

        Returns:
            Contract details
        """
        params = {"symbol": symbol} if symbol else None
        data = await self._request(
            "GET",
            Endpoints.CONTRACT_DETAIL,
            params=params,
            include_auth=False,
        )
        return ContractDetailResponse.model_validate(data)

    async def get_contract_depth(
        self, symbol: str, limit: int | None = None
    ) -> ContractDepthResponse:
        """Get contract's depth information (order book).

        Args:
            symbol: Contract symbol (e.g., "BTC_USDT")
            limit: Optional depth tier limit

        Returns:
            Order book with bids and asks
        """
        endpoint = f"{Endpoints.CONTRACT_DEPTH}/{symbol}"
        params = {"limit": limit} if limit else None
        data = await self._request("GET", endpoint, params=params, include_auth=False)
        return ContractDepthResponse.model_validate(data)

    async def test_connection(self) -> bool:
        """Test connection to the API using a public endpoint.

        Returns:
            True if connection is successful
        """
        try:
            await self.get_ticker("BTC_USDT")
            return True
        except Exception:
            return False


class MexcFuturesClientSync:
    """Synchronous wrapper for MexcFuturesClient.

    Provides a blocking API by running async methods in an event loop.
    Useful for scripts and simple applications that don't need async.

    Example:
        ```python
        client = MexcFuturesClientSync(config)
        ticker = client.get_ticker("BTC_USDT")
        print(ticker.data.lastPrice)
        client.close()
        ```
    """

    def __init__(self, config: SDKConfig):
        """Initialize the sync client wrapper.

        Args:
            config: SDK configuration
        """
        self._async_client = MexcFuturesClient(config)
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop for sync operations."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def _run(self, coro: Any) -> Any:
        """Run a coroutine synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(coro)

    def close(self) -> None:
        """Close the client."""
        self._run(self._async_client.close())

    def __enter__(self) -> MexcFuturesClientSync:
        # Generate user-agent once per session (via async client's __aenter__)
        self._run(self._async_client.__aenter__())
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    # Order methods
    def submit_order(self, order: SubmitOrderRequest) -> SubmitOrderResponse:
        return self._run(self._async_client.submit_order(order))

    def cancel_order(self, order_ids: list[int]) -> CancelOrderResponse:
        return self._run(self._async_client.cancel_order(order_ids))

    def cancel_order_by_external_id(
        self, request: CancelOrderByExternalIdRequest
    ) -> CancelOrderByExternalIdResponse:
        return self._run(self._async_client.cancel_order_by_external_id(request))

    def cancel_all_orders(
        self, request: CancelAllOrdersRequest | None = None
    ) -> CancelAllOrdersResponse:
        return self._run(self._async_client.cancel_all_orders(request))

    def get_order_history(self, params: OrderHistoryParams) -> OrderHistoryResponse:
        return self._run(self._async_client.get_order_history(params))

    def get_order_deals(self, params: OrderDealsParams) -> OrderDealsResponse:
        return self._run(self._async_client.get_order_deals(params))

    def get_order(self, order_id: int | str) -> GetOrderResponse:
        return self._run(self._async_client.get_order(order_id))

    def get_order_by_external_id(self, symbol: str, external_oid: str) -> GetOrderResponse:
        return self._run(self._async_client.get_order_by_external_id(symbol, external_oid))

    # Account methods
    def get_risk_limit(self) -> AccountResponse[list[RiskLimit]]:
        return self._run(self._async_client.get_risk_limit())

    def get_fee_rate(self) -> AccountResponse[list[FeeRate]]:
        return self._run(self._async_client.get_fee_rate())

    def get_account_asset(self, currency: str) -> AccountAssetResponse:
        return self._run(self._async_client.get_account_asset(currency))

    def get_open_positions(self, symbol: str | None = None) -> OpenPositionsResponse:
        return self._run(self._async_client.get_open_positions(symbol))

    def get_position_history(self, params: PositionHistoryParams) -> PositionHistoryResponse:
        return self._run(self._async_client.get_position_history(params))

    # Market methods
    def get_ticker(self, symbol: str) -> TickerResponse:
        return self._run(self._async_client.get_ticker(symbol))

    def get_contract_detail(self, symbol: str | None = None) -> ContractDetailResponse:
        return self._run(self._async_client.get_contract_detail(symbol))

    def get_contract_depth(self, symbol: str, limit: int | None = None) -> ContractDepthResponse:
        return self._run(self._async_client.get_contract_depth(symbol, limit))

    def test_connection(self) -> bool:
        return self._run(self._async_client.test_connection())

