"""Order-related data models for MEXC Futures API."""

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class OrderSide(IntEnum):
    """Order direction/side."""

    OPEN_LONG = 1
    CLOSE_SHORT = 2
    OPEN_SHORT = 3
    CLOSE_LONG = 4


class OrderType(IntEnum):
    """Order type."""

    LIMIT = 1
    POST_ONLY = 2
    IOC = 3  # Immediate or Cancel
    FOK = 4  # Fill or Kill
    MARKET = 5
    MARKET_TO_LIMIT = 6  # Convert market price to current price


class OpenType(IntEnum):
    """Position open type (margin mode)."""

    ISOLATED = 1
    CROSS = 2


class OrderCategory(IntEnum):
    """Order category."""

    LIMIT_ORDER = 1
    SYSTEM_TAKEOVER = 2
    CLOSE_DELEGATE = 3
    ADL_REDUCTION = 4


class OrderState(IntEnum):
    """Order state."""

    UNINFORMED = 1
    UNCOMPLETED = 2
    COMPLETED = 3
    CANCELLED = 4
    INVALID = 5


class PositionMode(IntEnum):
    """Position mode."""

    HEDGE = 1
    ONE_WAY = 2


# --- Order History ---


class OrderHistoryParams(BaseModel):
    """Parameters for fetching order history."""

    category: int
    page_num: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    states: int
    symbol: str


class Order(BaseModel):
    """Order information from history."""

    id: str
    symbol: str
    side: int
    type: str
    vol: float
    price: str
    leverage: int
    status: str
    createTime: int
    updateTime: int


class OrderHistoryData(BaseModel):
    """Order history data container."""

    orders: list[Order]
    total: int


class OrderHistoryResponse(BaseModel):
    """Response for order history request."""

    success: bool
    code: int
    data: OrderHistoryData


# --- Order Deals ---


class OrderDealsParams(BaseModel):
    """Parameters for fetching order deals/executions."""

    symbol: str
    start_time: int | None = None
    end_time: int | None = None
    page_num: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class OrderDeal(BaseModel):
    """Individual order deal/execution."""

    id: int
    symbol: str
    side: int  # 1=open long, 2=close short, 3=open short, 4=close long
    vol: str
    price: str
    fee: str
    feeCurrency: str
    profit: str
    isTaker: bool
    category: int  # 1=limit, 2=system takeover, 3=close delegate, 4=ADL
    orderId: int
    timestamp: int


class OrderDealsResponse(BaseModel):
    """Response for order deals request."""

    success: bool
    code: int
    data: list[OrderDeal]


# --- Cancel Orders ---


class CancelOrderResult(BaseModel):
    """Result of cancelling a single order."""

    orderId: int
    errorCode: int  # 0 = success
    errorMsg: str


class CancelOrderResponse(BaseModel):
    """Response for cancel order request."""

    success: bool
    code: int
    data: list[CancelOrderResult]


class CancelOrderByExternalIdRequest(BaseModel):
    """Request to cancel order by external ID."""

    symbol: str
    externalOid: str


class CancelOrderByExternalIdData(BaseModel):
    """Data returned when cancelling by external ID."""

    symbol: str
    externalOid: str


class CancelOrderByExternalIdResponse(BaseModel):
    """Response for cancel by external ID request."""

    success: bool
    code: int
    data: CancelOrderByExternalIdData | None = None


class CancelAllOrdersRequest(BaseModel):
    """Request to cancel all orders."""

    symbol: str | None = None


class CancelAllOrdersResponse(BaseModel):
    """Response for cancel all orders request."""

    success: bool
    code: int
    data: Any | None = None


# --- Submit Order ---


class SubmitOrderRequest(BaseModel):
    """Request to submit a new order."""

    symbol: str
    price: float
    vol: float
    side: OrderSide
    type: OrderType
    openType: OpenType
    leverage: int | None = None
    positionId: int | None = None
    externalOid: str | None = None
    stopLossPrice: float | None = None
    takeProfitPrice: float | None = None
    positionMode: PositionMode | None = None
    reduceOnly: bool | None = None


class SubmitOrderResponse(BaseModel):
    """Response for submit order request."""

    success: bool
    code: int
    message: str | None = None
    data: int | None = None  # Order ID


# --- Get Order ---


class GetOrderData(BaseModel):
    """Detailed order information."""

    orderId: str
    symbol: str
    positionId: int
    price: float
    vol: float
    leverage: int
    side: int
    category: int
    orderType: int
    dealAvgPrice: float
    dealVol: float
    orderMargin: float
    takerFee: float
    makerFee: float
    profit: float
    feeCurrency: str
    openType: int
    state: int
    externalOid: str
    errorCode: int
    usedMargin: float
    createTime: int
    updateTime: int


class GetOrderResponse(BaseModel):
    """Response for get order request."""

    success: bool
    code: int
    data: GetOrderData

