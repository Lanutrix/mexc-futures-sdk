"""Async WebSocket client for MEXC Futures real-time data."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any, Literal

import websockets
from websockets.asyncio.client import ClientConnection

from .constants import KLINE_INTERVALS, WEBSOCKET_URL, WsChannels
from .exceptions import MexcWebSocketError
from .utils import WebSocketConfig, get_logger

# Type alias for event callbacks
EventCallback = Callable[[Any], Coroutine[Any, Any, None]] | Callable[[Any], None]


class FilterType(str, Enum):
    """Personal data filter types."""

    ORDER = "order"
    ORDER_DEAL = "order.deal"
    POSITION = "position"
    PLAN_ORDER = "plan.order"
    STOP_ORDER = "stop.order"
    STOP_PLAN_ORDER = "stop.planorder"
    RISK_LIMIT = "risk.limit"
    ADL_LEVEL = "adl.level"
    ASSET = "asset"


class MexcFuturesWebSocket:
    """Async WebSocket client for MEXC Futures.

    Supports both public market data and private account data streams.
    Uses callbacks for event handling and supports auto-reconnect.

    Example:
        ```python
        ws = MexcFuturesWebSocket(config)

        @ws.on("ticker")
        async def handle_ticker(data):
            print(f"Price: {data['lastPrice']}")

        async with ws:
            await ws.subscribe_to_ticker("BTC_USDT")
            await asyncio.sleep(60)  # Listen for 60 seconds
        ```
    """

    def __init__(self, config: WebSocketConfig):
        """Initialize WebSocket client.

        Args:
            config: WebSocket configuration with API credentials
        """
        self.config = config
        self.logger = get_logger("mexc_futures.websocket", config.log_level)

        self._ws: ClientConnection | None = None
        self._is_connected = False
        self._is_logged_in = False
        self._should_reconnect = config.auto_reconnect

        self._ping_task: asyncio.Task[None] | None = None
        self._recv_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None

        # Event callbacks: event_name -> list of callbacks
        self._callbacks: dict[str, list[EventCallback]] = {}

    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._is_connected

    @property
    def logged_in(self) -> bool:
        """Check if user is logged in for private data."""
        return self._is_logged_in

    def on(self, event: str) -> Callable[[EventCallback], EventCallback]:
        """Decorator to register an event callback.

        Args:
            event: Event name to listen for

        Returns:
            Decorator function

        Example:
            ```python
            @ws.on("ticker")
            async def handle_ticker(data):
                print(data)
            ```
        """

        def decorator(func: EventCallback) -> EventCallback:
            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(func)
            return func

        return decorator

    def add_callback(self, event: str, callback: EventCallback) -> None:
        """Add a callback for an event.

        Args:
            event: Event name
            callback: Callback function (sync or async)
        """
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: EventCallback) -> None:
        """Remove a callback for an event.

        Args:
            event: Event name
            callback: Callback function to remove
        """
        if event in self._callbacks:
            self._callbacks[event] = [cb for cb in self._callbacks[event] if cb != callback]

    async def _emit(self, event: str, data: Any) -> None:
        """Emit an event to all registered callbacks.

        Args:
            event: Event name
            data: Event data
        """
        callbacks = self._callbacks.get(event, [])
        for callback in callbacks:
            try:
                result = callback(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self.logger.error(f"Error in callback for '{event}': {e}")

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        self.logger.info("Connecting to MEXC Futures WebSocket...")

        try:
            self._ws = await websockets.connect(
                WEBSOCKET_URL,
                proxy=self.config.proxy,
            )
            self._is_connected = True
            self.logger.info("WebSocket connected")

            # Start background tasks
            self._ping_task = asyncio.create_task(self._ping_loop())
            self._recv_task = asyncio.create_task(self._receive_loop())

            await self._emit("connected", None)

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise MexcWebSocketError(f"Failed to connect: {e}", e) from e

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self.logger.info("Disconnecting WebSocket...")
        self._should_reconnect = False

        # Cancel background tasks
        for task in [self._ping_task, self._recv_task, self._reconnect_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

        self._is_connected = False
        self._is_logged_in = False

    async def __aenter__(self) -> MexcFuturesWebSocket:
        """Enter async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.disconnect()

    async def _send(self, message: dict[str, Any]) -> None:
        """Send a message to WebSocket.

        Args:
            message: Message dict to send
        """
        if not self._ws or not self._is_connected:
            self.logger.error("Cannot send: WebSocket not connected")
            return

        msg_str = json.dumps(message)
        self.logger.debug(f"Sending: {msg_str}")
        await self._ws.send(msg_str)

    async def _ping_loop(self) -> None:
        """Background task to send periodic pings."""
        while self._is_connected:
            try:
                await asyncio.sleep(self.config.ping_interval)
                if self._is_connected:
                    await self._send({"method": "ping"})
                    self.logger.debug("Ping sent")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Ping error: {e}")

    async def _receive_loop(self) -> None:
        """Background task to receive and process messages."""
        while self._is_connected and self._ws:
            try:
                message = await self._ws.recv()
                data = json.loads(message)
                self.logger.debug(f"Received: {message}")
                await self._handle_message(data)

            except websockets.ConnectionClosed as e:
                self.logger.warning(f"WebSocket closed: {e.code} {e.reason}")
                self._is_connected = False
                self._is_logged_in = False
                await self._emit("disconnected", {"code": e.code, "reason": e.reason})

                if self._should_reconnect:
                    await self._schedule_reconnect()
                break

            except asyncio.CancelledError:
                break
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {e}")
            except Exception as e:
                self.logger.error(f"Receive error: {e}")
                await self._emit("error", e)

    async def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt."""
        self.logger.info(f"Reconnecting in {self.config.reconnect_interval}s...")
        await asyncio.sleep(self.config.reconnect_interval)

        try:
            await self.connect()
        except Exception as e:
            self.logger.error(f"Reconnect failed: {e}")
            if self._should_reconnect:
                await self._schedule_reconnect()

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle incoming WebSocket message.

        Args:
            message: Parsed JSON message
        """
        channel = message.get("channel")

        # Pong response
        if channel == "pong":
            await self._emit("pong", message.get("data"))
            return

        # Login response
        if channel == "rs.login":
            data = message.get("data")
            if data == "success" or (isinstance(data, dict) and data.get("code") == 0):
                self._is_logged_in = True
                self.logger.info("Login successful")
                await self._emit("login", message)
            else:
                self._is_logged_in = False
                self.logger.error(f"Login failed: {data}")
                await self._emit("login_failed", data)
            return

        # Filter response
        if channel == "rs.personal.filter":
            data = message.get("data")
            if data == "success" or (isinstance(data, dict) and data.get("code") == 0):
                self.logger.info("Filter set successfully")
                await self._emit("filter_set", data)
            else:
                self.logger.error(f"Filter set failed: {data}")
                await self._emit("filter_failed", data)
            return

        # Subscription confirmations
        if channel and channel.startswith("rs.sub."):
            stream_type = channel.replace("rs.sub.", "")
            self.logger.info(f"Subscribed to {stream_type}")
            await self._emit("subscribed", {"type": stream_type, "data": message.get("data")})
            return

        # Unsubscription confirmations
        if channel and channel.startswith("rs.unsub."):
            stream_type = channel.replace("rs.unsub.", "")
            self.logger.info(f"Unsubscribed from {stream_type}")
            await self._emit("unsubscribed", {"type": stream_type, "data": message.get("data")})
            return

        # Error response
        if channel == "rs.error":
            self.logger.error(f"WebSocket error: {message.get('data')}")
            await self._emit("error", Exception(str(message.get("data"))))
            return

        # Data updates
        await self._handle_data_update(message)

    async def _handle_data_update(self, message: dict[str, Any]) -> None:
        """Handle data update messages.

        Args:
            message: Parsed message with channel and data
        """
        channel = message.get("channel")
        data = message.get("data")

        # Map channels to event names
        channel_map = {
            WsChannels.TICKERS: "tickers",
            WsChannels.TICKER: "ticker",
            WsChannels.DEAL: "deal",
            WsChannels.DEPTH: "depth",
            WsChannels.KLINE: "kline",
            WsChannels.FUNDING_RATE: "funding_rate",
            WsChannels.INDEX_PRICE: "index_price",
            WsChannels.FAIR_PRICE: "fair_price",
            WsChannels.ORDER: "order_update",
            WsChannels.ORDER_DEAL: "order_deal",
            WsChannels.POSITION: "position_update",
            WsChannels.ASSET: "asset_update",
            WsChannels.STOP_ORDER: "stop_order",
            WsChannels.STOP_PLAN_ORDER: "stop_plan_order",
            WsChannels.LIQUIDATE_RISK: "liquidate_risk",
            WsChannels.ADL_LEVEL: "adl_level",
            WsChannels.RISK_LIMIT: "risk_limit",
            WsChannels.PLAN_ORDER: "plan_order",
        }

        event_name = channel_map.get(channel)
        if event_name:
            await self._emit(event_name, data)
        else:
            # Generic message event for unhandled channels
            await self._emit("message", message)

    # ==================== AUTHENTICATION ====================

    async def login(self, subscribe: bool = True) -> None:
        """Login to access private data streams.

        Args:
            subscribe: If False, cancels default push of all private data

        Raises:
            MexcWebSocketError: If not connected
        """
        if not self._is_connected:
            raise MexcWebSocketError("WebSocket not connected")

        # Generate HMAC-SHA256 signature
        req_time = str(int(time.time() * 1000))
        signature_string = f"{self.config.api_key}{req_time}"
        signature = hmac.new(
            self.config.secret_key.encode(),
            signature_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        await self._send(
            {
                "subscribe": subscribe,
                "method": "login",
                "param": {
                    "apiKey": self.config.api_key,
                    "signature": signature,
                    "reqTime": req_time,
                },
            }
        )

    async def set_personal_filter(
        self,
        filters: list[dict[str, Any]] | None = None,
    ) -> None:
        """Set personal data filters.

        Args:
            filters: List of filter configs. Empty list means all data.

        Raises:
            MexcWebSocketError: If not logged in
        """
        if not self._is_logged_in:
            raise MexcWebSocketError("Must login first before setting filters")

        await self._send(
            {
                "method": "personal.filter",
                "param": {"filters": filters or []},
            }
        )

    # ==================== PRIVATE DATA SUBSCRIPTIONS ====================

    async def subscribe_to_orders(self, symbols: list[str] | None = None) -> None:
        """Subscribe to order updates.

        Args:
            symbols: Optional list of symbols to filter
        """
        await self.set_personal_filter([{"filter": FilterType.ORDER.value, "rules": symbols}])

    async def subscribe_to_order_deals(self, symbols: list[str] | None = None) -> None:
        """Subscribe to order deals/executions.

        Args:
            symbols: Optional list of symbols to filter
        """
        await self.set_personal_filter([{"filter": FilterType.ORDER_DEAL.value, "rules": symbols}])

    async def subscribe_to_positions(self, symbols: list[str] | None = None) -> None:
        """Subscribe to position updates.

        Args:
            symbols: Optional list of symbols to filter
        """
        await self.set_personal_filter([{"filter": FilterType.POSITION.value, "rules": symbols}])

    async def subscribe_to_assets(self) -> None:
        """Subscribe to asset/balance updates."""
        await self.set_personal_filter([{"filter": FilterType.ASSET.value}])

    async def subscribe_to_adl_levels(self) -> None:
        """Subscribe to ADL level updates."""
        await self.set_personal_filter([{"filter": FilterType.ADL_LEVEL.value}])

    async def subscribe_to_all_private(self) -> None:
        """Subscribe to all private data (default after login)."""
        await self.set_personal_filter([])

    # ==================== PUBLIC DATA SUBSCRIPTIONS ====================

    async def subscribe_to_all_tickers(self, gzip: bool = False) -> None:
        """Subscribe to all contract tickers.

        Args:
            gzip: Whether to compress data
        """
        await self._send({"method": "sub.tickers", "param": {}, "gzip": gzip})

    async def unsubscribe_from_all_tickers(self) -> None:
        """Unsubscribe from all tickers."""
        await self._send({"method": "unsub.tickers", "param": {}})

    async def subscribe_to_ticker(self, symbol: str) -> None:
        """Subscribe to ticker for a specific contract.

        Args:
            symbol: Contract symbol (e.g., "BTC_USDT")
        """
        await self._send({"method": "sub.ticker", "param": {"symbol": symbol}})

    async def unsubscribe_from_ticker(self, symbol: str) -> None:
        """Unsubscribe from ticker for a specific contract.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.ticker", "param": {"symbol": symbol}})

    async def subscribe_to_deals(self, symbol: str) -> None:
        """Subscribe to trades for a specific contract.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "sub.deal", "param": {"symbol": symbol}})

    async def unsubscribe_from_deals(self, symbol: str) -> None:
        """Unsubscribe from trades.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.deal", "param": {"symbol": symbol}})

    async def subscribe_to_depth(self, symbol: str, compress: bool = False) -> None:
        """Subscribe to incremental depth for a contract.

        Args:
            symbol: Contract symbol
            compress: Whether to compress data
        """
        await self._send({"method": "sub.depth", "param": {"symbol": symbol, "compress": compress}})

    async def subscribe_to_full_depth(
        self, symbol: str, limit: Literal[5, 10, 20] = 20
    ) -> None:
        """Subscribe to full depth for a contract.

        Args:
            symbol: Contract symbol
            limit: Depth limit (5, 10, or 20)
        """
        await self._send({"method": "sub.depth.full", "param": {"symbol": symbol, "limit": limit}})

    async def unsubscribe_from_depth(self, symbol: str) -> None:
        """Unsubscribe from incremental depth.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.depth", "param": {"symbol": symbol}})

    async def unsubscribe_from_full_depth(self, symbol: str) -> None:
        """Unsubscribe from full depth.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "usub.depth.full", "param": {"symbol": symbol}})

    async def subscribe_to_kline(
        self,
        symbol: str,
        interval: str,
    ) -> None:
        """Subscribe to kline/candlestick data.

        Args:
            symbol: Contract symbol
            interval: Kline interval (Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1)

        Raises:
            ValueError: If interval is invalid
        """
        if interval not in KLINE_INTERVALS:
            raise ValueError(f"Invalid interval. Must be one of: {KLINE_INTERVALS}")

        await self._send({"method": "sub.kline", "param": {"symbol": symbol, "interval": interval}})

    async def unsubscribe_from_kline(self, symbol: str) -> None:
        """Unsubscribe from kline data.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.kline", "param": {"symbol": symbol}})

    async def subscribe_to_funding_rate(self, symbol: str) -> None:
        """Subscribe to funding rate for a contract.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "sub.funding.rate", "param": {"symbol": symbol}})

    async def unsubscribe_from_funding_rate(self, symbol: str) -> None:
        """Unsubscribe from funding rate.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.funding.rate", "param": {"symbol": symbol}})

    async def subscribe_to_index_price(self, symbol: str) -> None:
        """Subscribe to index price for a contract.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "sub.index.price", "param": {"symbol": symbol}})

    async def unsubscribe_from_index_price(self, symbol: str) -> None:
        """Unsubscribe from index price.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.index.price", "param": {"symbol": symbol}})

    async def subscribe_to_fair_price(self, symbol: str) -> None:
        """Subscribe to fair price for a contract.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "sub.fair.price", "param": {"symbol": symbol}})

    async def unsubscribe_from_fair_price(self, symbol: str) -> None:
        """Unsubscribe from fair price.

        Args:
            symbol: Contract symbol
        """
        await self._send({"method": "unsub.fair.price", "param": {"symbol": symbol}})

