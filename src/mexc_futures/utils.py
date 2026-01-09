"""Utility functions for MEXC Futures SDK."""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any


def get_logger(name: str = "mexc_futures", level: int = logging.WARNING) -> logging.Logger:
    """Get or create a logger with the specified name and level.

    Args:
        name: Logger name (default: "mexc_futures")
        level: Logging level (default: WARNING)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


def mexc_crypto(key: str, obj: Any) -> dict[str, str]:
    """Generate MEXC crypto signature using MD5 algorithm.

    This replicates the browser's signature generation:
    1. timestamp = current time in milliseconds
    2. g = md5(key + timestamp)[7:]  (substring from index 7)
    3. s = JSON stringified request object
    4. sign = md5(timestamp + s + g)

    Args:
        key: WEB authentication key
        obj: Request object to sign

    Returns:
        Dict with 'time' (timestamp) and 'sign' (signature)
    """
    timestamp = str(int(time.time() * 1000))

    # g = md5(key + timestamp), take from index 7 onwards
    g = hashlib.md5((key + timestamp).encode()).hexdigest()[7:]

    # Serialize object to JSON (compact, no spaces)
    s = json.dumps(obj, separators=(",", ":"))

    # sign = md5(timestamp + json + g)
    sign = hashlib.md5((timestamp + s + g).encode()).hexdigest()

    return {"time": timestamp, "sign": sign}


@dataclass
class SDKConfig:
    """Configuration for MEXC Futures SDK."""

    auth_token: str
    """WEB authentication token from browser (starts with 'WEB...')"""

    base_url: str = "https://futures.mexc.com/api/v1"
    """Base URL for the API"""

    timeout: float = 30.0
    """Request timeout in seconds"""

    user_agent: str | None = None
    """Custom User-Agent header"""

    custom_headers: dict[str, str] = field(default_factory=dict)
    """Additional custom headers"""

    log_level: int = logging.WARNING
    """Logging level (use logging.DEBUG, logging.INFO, etc.)"""


@dataclass
class WebSocketConfig:
    """Configuration for MEXC Futures WebSocket."""

    api_key: str
    """API Key from MEXC API management"""

    secret_key: str
    """Secret Key for HMAC signature"""

    auto_reconnect: bool = True
    """Whether to automatically reconnect on disconnect"""

    reconnect_interval: float = 5.0
    """Seconds to wait before reconnecting"""

    ping_interval: float = 15.0
    """Seconds between ping messages (recommended: 10-20)"""

    log_level: int = logging.WARNING
    """Logging level"""

