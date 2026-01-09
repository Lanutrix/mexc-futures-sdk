"""Exception classes for MEXC Futures SDK."""

from datetime import datetime, timezone
from typing import Any


class MexcFuturesError(Exception):
    """Base exception for MEXC Futures SDK."""

    def __init__(
        self,
        message: str,
        code: str | int | None = None,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.original_error = original_error
        self.timestamp = datetime.now(timezone.utc)

    @property
    def user_friendly_message(self) -> str:
        """Get a user-friendly error message."""
        return self.message

    def get_details(self) -> dict[str, Any]:
        """Get error details for logging."""
        return {
            "name": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class MexcAuthenticationError(MexcFuturesError):
    """Authentication related errors."""

    def __init__(self, message: str | None = None, original_error: Exception | None = None):
        default_message = "Authentication failed. Please check your authorization token."
        super().__init__(
            message=message or default_message,
            code="AUTH_ERROR",
            status_code=401,
            original_error=original_error,
        )

    @property
    def user_friendly_message(self) -> str:
        if self.status_code == 401:
            return (
                "Authentication failed. Your authorization token may be expired or invalid. "
                "Please update your WEB token from browser Developer Tools."
            )
        return f"Authentication error: {self.message}"


class MexcApiError(MexcFuturesError):
    """API related errors (4xx, 5xx responses)."""

    def __init__(
        self,
        message: str,
        code: str | int,
        status_code: int,
        endpoint: str | None = None,
        method: str | None = None,
        response_data: Any = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message, code=code, status_code=status_code, original_error=original_error
        )
        self.endpoint = endpoint
        self.method = method
        self.response_data = response_data

    @property
    def user_friendly_message(self) -> str:
        messages = {
            400: f"Bad Request: {self.message}. Please check your request parameters.",
            401: f"Unauthorized: {self.message}. Your authorization token may be expired.",
            403: f"Forbidden: {self.message}. You don't have permission for this operation.",
            404: f"Not Found: {self.message}. The requested resource was not found.",
            429: f"Rate Limit Exceeded: {self.message}. Please reduce request frequency.",
            500: f"Server Error: {self.message}. MEXC server is experiencing issues.",
            502: f"Service Unavailable: {self.message}. MEXC service is temporarily unavailable.",
            503: f"Service Unavailable: {self.message}. MEXC service is temporarily unavailable.",
            504: f"Service Unavailable: {self.message}. MEXC service is temporarily unavailable.",
        }
        return messages.get(self.status_code or 0, f"API Error ({self.status_code}): {self.message}")

    def get_details(self) -> dict[str, Any]:
        details = super().get_details()
        details.update(
            {
                "endpoint": self.endpoint,
                "method": self.method,
                "response_data": self.response_data,
            }
        )
        return details


class MexcNetworkError(MexcFuturesError):
    """Network related errors (timeouts, connection issues)."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(
            message=message, code="NETWORK_ERROR", status_code=None, original_error=original_error
        )

    @property
    def user_friendly_message(self) -> str:
        if "timeout" in self.message.lower():
            return "Request timeout. Please check your internet connection and try again."
        if "ENOTFOUND" in self.message or "ECONNREFUSED" in self.message:
            return "Connection failed. Please check your internet connection."
        return f"Network error: {self.message}"


class MexcValidationError(MexcFuturesError):
    """Validation errors for request parameters."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field

    @property
    def user_friendly_message(self) -> str:
        if self.field:
            return f"Validation error for field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"


class MexcSignatureError(MexcFuturesError):
    """Signature related errors."""

    def __init__(self, message: str | None = None, original_error: Exception | None = None):
        default_message = "Request signature verification failed"
        super().__init__(
            message=message or default_message,
            code="SIGNATURE_ERROR",
            status_code=602,
            original_error=original_error,
        )

    @property
    def user_friendly_message(self) -> str:
        return (
            "Signature verification failed. This usually means your authorization token "
            "is invalid or expired. Please get a fresh WEB token from your browser."
        )


class MexcRateLimitError(MexcFuturesError):
    """Rate limiting errors."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(
            message=message, code="RATE_LIMIT", status_code=429, original_error=original_error
        )
        self.retry_after = retry_after

    @property
    def user_friendly_message(self) -> str:
        retry_msg = f" Please retry after {self.retry_after} seconds." if self.retry_after else ""
        return f"Rate limit exceeded: {self.message}.{retry_msg}"


class MexcWebSocketError(MexcFuturesError):
    """WebSocket connection errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(
            message=message, code="WEBSOCKET_ERROR", status_code=None, original_error=original_error
        )


def parse_httpx_error(
    error: Exception,
    endpoint: str | None = None,
    method: str | None = None,
) -> MexcFuturesError:
    """Parse httpx error and convert to appropriate MEXC error."""
    import httpx

    error_message = str(error)

    # Network errors
    if isinstance(error, httpx.ConnectError):
        return MexcNetworkError(error_message, error)

    if isinstance(error, httpx.TimeoutException):
        return MexcNetworkError("Request timeout", error)

    # Response errors
    if isinstance(error, httpx.HTTPStatusError):
        response = error.response
        status = response.status_code

        try:
            data = response.json()
            message = data.get("message", error_message)
            code = data.get("code", status)
        except Exception:
            message = error_message
            code = status
            data = None

        # Specific error types
        if status == 401:
            return MexcAuthenticationError(message, error)
        if status == 429:
            retry_after = response.headers.get("retry-after")
            return MexcRateLimitError(
                message, int(retry_after) if retry_after else None, error
            )

        # Check for signature error
        if code == 602 or "signature" in message.lower():
            return MexcSignatureError(message, error)

        return MexcApiError(
            message=message,
            code=code,
            status_code=status,
            endpoint=endpoint,
            method=method,
            response_data=data,
            original_error=error,
        )

    # Fallback
    return MexcFuturesError(error_message, code="UNKNOWN_ERROR", original_error=error)


def format_error_for_logging(error: MexcFuturesError) -> str:
    """Format error for logging."""
    import json

    details = error.get_details()
    return f"{error.user_friendly_message}\nDetails: {json.dumps(details, indent=2, default=str)}"

