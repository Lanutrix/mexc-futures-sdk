"""Market data models for MEXC Futures API."""

from pydantic import BaseModel


class RiseFallRates(BaseModel):
    """Price change rates over various time periods."""

    zone: str
    r: float  # current rate
    v: float  # current value
    r7: float  # 7 days rate
    r30: float  # 30 days rate
    r90: float  # 90 days rate
    r180: float  # 180 days rate
    r365: float  # 365 days rate


class TickerData(BaseModel):
    """Ticker/market data for a contract."""

    contractId: int
    symbol: str
    lastPrice: float
    bid1: float
    ask1: float
    volume24: float
    amount24: float
    holdVol: float  # open interest
    lower24Price: float
    high24Price: float
    riseFallRate: float
    riseFallValue: float
    indexPrice: float
    fairPrice: float
    fundingRate: float
    maxBidPrice: float
    minAskPrice: float
    timestamp: int
    riseFallRates: RiseFallRates
    riseFallRatesOfTimezone: list[float]


class TickerResponse(BaseModel):
    """Response for ticker request."""

    success: bool
    code: int
    data: TickerData


class ContractDetail(BaseModel):
    """Contract/trading pair details."""

    symbol: str
    displayName: str
    displayNameEn: str
    positionOpenType: int  # 1=isolated, 2=cross, 3=both
    baseCoin: str
    quoteCoin: str
    settleCoin: str
    contractSize: float
    minLeverage: int
    maxLeverage: int
    priceScale: int
    volScale: int
    amountScale: int
    priceUnit: float
    volUnit: float
    minVol: float
    maxVol: float
    bidLimitPriceRate: float
    askLimitPriceRate: float
    takerFeeRate: float
    makerFeeRate: float
    maintenanceMarginRate: float
    initialMarginRate: float
    riskBaseVol: float
    riskIncrVol: float
    riskIncrMmr: float
    riskIncrImr: float
    riskLevelLimit: int
    priceCoefficientVariation: float
    indexOrigin: list[str]
    state: int  # 0=enabled, 1=delivery, 2=completed, 3=offline, 4=pause
    isNew: bool
    isHot: bool
    isHidden: bool
    conceptPlate: list[str]
    riskLimitType: str  # "BY_VOLUME" or "BY_VALUE"
    maxNumOrders: list[int]
    marketOrderMaxLevel: int
    marketOrderPriceLimitRate1: float
    marketOrderPriceLimitRate2: float
    triggerProtect: float
    appraisal: float
    showAppraisalCountdown: int
    automaticDelivery: int
    apiAllowed: bool


class ContractDetailResponse(BaseModel):
    """Response for contract detail request."""

    success: bool
    code: int
    data: ContractDetail | list[ContractDetail]


class DepthEntry(BaseModel):
    """Single depth entry (price level)."""

    price: float
    volume: float
    count: int | None = None


class ContractDepthData(BaseModel):
    """Order book depth data."""

    asks: list[DepthEntry]  # seller depth (ascending)
    bids: list[DepthEntry]  # buyer depth (descending)
    version: int
    timestamp: int


class ContractDepthResponse(BaseModel):
    """Response for contract depth request.

    Note: This endpoint may return data in different formats.
    """

    success: bool | None = None
    code: int | None = None
    data: ContractDepthData | None = None
    # Direct response format fallback
    asks: list[list[float]] | None = None
    bids: list[list[float]] | None = None
    version: int | None = None
    timestamp: int | None = None

    def get_depth(self) -> ContractDepthData | None:
        """Get depth data regardless of response format."""
        if self.data:
            return self.data
        if self.asks is not None and self.bids is not None:
            return ContractDepthData(
                asks=[
                    DepthEntry(price=e[0], volume=e[1], count=int(e[2]) if len(e) > 2 else None)
                    for e in self.asks
                ],
                bids=[
                    DepthEntry(price=e[0], volume=e[1], count=int(e[2]) if len(e) > 2 else None)
                    for e in self.bids
                ],
                version=self.version or 0,
                timestamp=self.timestamp or 0,
            )
        return None

