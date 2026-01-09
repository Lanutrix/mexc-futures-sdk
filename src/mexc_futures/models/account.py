"""Account-related data models for MEXC Futures API."""

from enum import IntEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PositionType(IntEnum):
    """Position type (direction)."""

    LONG = 1
    SHORT = 2


class PositionState(IntEnum):
    """Position state."""

    HOLDING = 1
    SYSTEM_AUTO_HOLDING = 2
    CLOSED = 3


class RiskLimit(BaseModel):
    """Risk limit configuration for a symbol."""

    symbol: str
    level: int
    maxLeverage: int
    riskLimit: float
    maintMarginRate: float


class FeeRate(BaseModel):
    """Fee rate configuration for a symbol."""

    symbol: str
    takerFeeRate: float
    makerFeeRate: float


class AccountResponse(BaseModel, Generic[T]):
    """Generic account response wrapper."""

    success: bool
    code: int
    data: T


class AccountAsset(BaseModel):
    """User's single currency asset information."""

    currency: str
    positionMargin: float
    availableBalance: float
    cashBalance: float
    frozenBalance: float
    equity: float
    unrealized: float
    bonus: float


class AccountAssetResponse(BaseModel):
    """Response for account asset request."""

    success: bool
    code: int
    data: AccountAsset


class Position(BaseModel):
    """User's position information."""

    positionId: int
    symbol: str
    positionType: int  # 1=long, 2=short
    openType: int  # 1=isolated, 2=cross
    state: int  # 1=holding, 2=system auto-holding, 3=closed
    holdVol: float
    frozenVol: float
    closeVol: float
    holdAvgPrice: float
    openAvgPrice: float
    closeAvgPrice: float
    liquidatePrice: float
    oim: float  # original initial margin
    adlLevel: int | None = None  # ADL level 1-5
    im: float  # initial margin
    holdFee: float  # positive=received, negative=paid
    realised: float  # realized PnL
    leverage: int
    createTime: int
    updateTime: int
    autoAddIm: bool | None = None


class OpenPositionsResponse(BaseModel):
    """Response for open positions request."""

    success: bool
    code: int
    data: list[Position]


class PositionHistoryParams(BaseModel):
    """Parameters for fetching position history."""

    symbol: str | None = None
    type: int | None = Field(None, ge=1, le=2)  # 1=long, 2=short
    page_num: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PositionHistoryResponse(BaseModel):
    """Response for position history request."""

    success: bool
    code: int
    message: str
    data: list[Position]

