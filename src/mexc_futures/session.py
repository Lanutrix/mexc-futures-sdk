"""HTTP session manager with keep-alive, HTTP/2, and TLS 1.3 support."""

from __future__ import annotations

import asyncio
import ssl
from typing import TYPE_CHECKING

import httpx

from .utils import get_logger

if TYPE_CHECKING:
    from .utils import SDKConfig

WARMUP_ENDPOINT = "/contract/ticker"
WARMUP_PARAMS = {"symbol": "BTC_USDT"}


class SessionManager:
    """Manages a persistent httpx.AsyncClient with background keep-alive.

    Creates an HTTP/2 client over TLS 1.3 through the configured proxy,
    warms up the connection on first use, and keeps it alive by pinging
    a lightweight public endpoint every ``config.ping_interval`` seconds.

    If ``config.max_idle_pings`` consecutive pings fire without any real
    API activity, the session is closed.  The next ``get_client()`` call
    transparently creates a new session and warms it up again.
    """

    def __init__(self, config: SDKConfig) -> None:
        self._config = config
        self._logger = get_logger("mexc_futures.session", config.log_level)
        self._client: httpx.AsyncClient | None = None
        self._ping_task: asyncio.Task[None] | None = None
        self._idle_ping_count: int = 0
        self._lock = asyncio.Lock()

    @property
    def is_active(self) -> bool:
        """True when the underlying client exists and is not closed."""
        return self._client is not None and not self._client.is_closed

    async def get_client(self) -> httpx.AsyncClient:
        """Return a warmed-up HTTP client, creating one if needed."""
        async with self._lock:
            if not self.is_active:
                self._client = self._create_client()
                await self._warmup()
                self._start_keepalive()
            return self._client  # type: ignore[return-value]

    def notify_activity(self) -> None:
        """Reset the idle-ping counter (call on every real API request)."""
        self._idle_ping_count = 0

    async def close(self) -> None:
        """Cancel keep-alive and close the HTTP client."""
        self._cancel_ping_task()
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_client(self) -> httpx.AsyncClient:
        cfg = self._config

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_3

        timeout = httpx.Timeout(
            connect=cfg.connect_timeout,
            read=cfg.read_timeout,
            write=cfg.write_timeout,
            pool=cfg.pool_timeout,
        )

        limits = httpx.Limits(
            max_connections=cfg.max_connections,
            max_keepalive_connections=cfg.max_keepalive_connections,
            keepalive_expiry=cfg.keepalive_expiry,
        )

        self._logger.debug(
            "Creating httpx client  http2=%s  proxy=%s  keepalive_expiry=%s",
            cfg.http2,
            cfg.proxy,
            cfg.keepalive_expiry,
        )

        return httpx.AsyncClient(
            base_url=cfg.base_url,
            proxy=cfg.proxy,
            http2=cfg.http2,
            timeout=timeout,
            limits=limits,
            verify=ssl_ctx,
        )

    async def _warmup(self) -> None:
        """Pre-establish TCP + TLS + HTTP/2 to avoid cold-start latency."""
        assert self._client is not None
        self._logger.info("Warming up session (TCP + SOCKS5 + TLS 1.3 + HTTP/2)…")
        try:
            resp = await self._client.get(WARMUP_ENDPOINT, params=WARMUP_PARAMS)
            resp.raise_for_status()
            self._logger.info("Session warm-up complete")
        except Exception as exc:
            self._logger.warning("Warm-up request failed: %s", exc)

    # ------------------------------------------------------------------
    # Keep-alive loop
    # ------------------------------------------------------------------

    def _start_keepalive(self) -> None:
        self._idle_ping_count = 0
        self._cancel_ping_task()
        self._ping_task = asyncio.create_task(self._keepalive_loop())

    def _cancel_ping_task(self) -> None:
        if self._ping_task is not None and not self._ping_task.done():
            self._ping_task.cancel()
        self._ping_task = None

    async def _keepalive_loop(self) -> None:
        cfg = self._config
        try:
            while True:
                await asyncio.sleep(cfg.ping_interval)

                if self._idle_ping_count >= cfg.max_idle_pings:
                    self._logger.info(
                        "Session idle for %d pings — letting it expire",
                        self._idle_ping_count,
                    )
                    await self._close_client()
                    return

                if not self.is_active:
                    return

                try:
                    resp = await self._client.get(  # type: ignore[union-attr]
                        WARMUP_ENDPOINT, params=WARMUP_PARAMS
                    )
                    resp.raise_for_status()
                    self._idle_ping_count += 1
                    self._logger.debug(
                        "Keep-alive ping %d/%d OK",
                        self._idle_ping_count,
                        cfg.max_idle_pings,
                    )
                except Exception as exc:
                    self._logger.warning("Keep-alive ping failed: %s", exc)
                    await self._close_client()
                    return

        except asyncio.CancelledError:
            return

    async def _close_client(self) -> None:
        """Close the client without acquiring the lock (called from within the loop)."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
