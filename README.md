# MEXC Futures SDK for Python

Python SDK для работы с MEXC Futures API. Поддерживает асинхронные и синхронные операции, REST API и WebSocket потоки данных.

## Установка

```bash
pip install mexc-futures
```

Или с помощью uv:

```bash
uv add mexc-futures
```

Для разработки:

```bash
git clone https://github.com/Lanutrix/mexc-futures-sdk
cd mexc-futures-sdk
uv sync --dev
```

## Быстрый старт

### Асинхронный клиент (рекомендуется)

```python
import asyncio
from mexc_futures import MexcFuturesClient, SDKConfig

async def main():
    config = SDKConfig(auth_token="WEB...")
    
    async with MexcFuturesClient(config) as client:
        # Получить текущую цену BTC
        ticker = await client.get_ticker("BTC_USDT")
        print(f"BTC цена: {ticker.data.lastPrice}")
        
        # Проверить баланс
        asset = await client.get_account_asset("USDT")
        print(f"Доступно: {asset.data.availableBalance} USDT")

asyncio.run(main())
```

### Синхронный клиент

```python
from mexc_futures import MexcFuturesClientSync, SDKConfig

config = SDKConfig(auth_token="WEB...")

with MexcFuturesClientSync(config) as client:
    ticker = client.get_ticker("BTC_USDT")
    print(f"BTC цена: {ticker.data.lastPrice}")
```

## Конфигурация

### SDKConfig (REST API)

```python
from mexc_futures import SDKConfig
import logging

config = SDKConfig(
    auth_token="WEB...",           # Обязательно: токен авторизации
    base_url="https://futures.mexc.com/api/v1",  # Базовый URL
    timeout=30.0,                  # Таймаут запросов (секунды)
    user_agent=None,               # Кастомный User-Agent (или авто)
    custom_headers={},             # Дополнительные заголовки
    custom_cookies={},             # Дополнительные cookies
    log_level=logging.WARNING,     # Уровень логирования
)
```

`custom_cookies` можно использовать для передачи дополнительных браузерных cookies (например, локаль или другие параметры сессии). Они добавляются ко всем HTTP-запросам клиента.

### User-Agent

По умолчанию user-agent генерируется автоматически при входе в контекст `with` с помощью библиотеки [fake-useragent](https://pypi.org/project/fake-useragent/). Каждая сессия получает свой уникальный user-agent:

```python
import asyncio
from mexc_futures import MexcFuturesClient, SDKConfig

async def session(name: str):
    config = SDKConfig(auth_token="WEB...")
    async with MexcFuturesClient(config) as client:
        print(f"{name}: {client._user_agent}")
        # User-agent сохраняется для всех запросов внутри with

# Параллельные сессии с разными user-agent
async def main():
    await asyncio.gather(
        session("Session 1"),
        session("Session 2"),
        session("Session 3"),
    )

asyncio.run(main())
```

Для использования своего user-agent:

```python
config = SDKConfig(
    auth_token="WEB...",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135.0.0.0"
)
```

### WebSocketConfig

```python
from mexc_futures import WebSocketConfig

ws_config = WebSocketConfig(
    api_key="mx0...",              # API ключ из настроек MEXC
    secret_key="...",              # Секретный ключ для подписи
    auto_reconnect=True,           # Автопереподключение
    reconnect_interval=5.0,        # Интервал переподключения (сек)
    ping_interval=15.0,            # Интервал ping (рекомендуется 10-20)
    log_level=logging.WARNING,
)
```

### Получение токена авторизации

WEB токен можно получить из браузера:
1. Откройте https://futures.mexc.com
2. Войдите в аккаунт
3. Откройте DevTools (F12) → Network
4. Найдите запрос к API и скопируйте заголовок `Authorization`

## REST API

### Работа с ордерами

#### Создание ордера

```python
from mexc_futures import (
    MexcFuturesClient, SDKConfig,
    SubmitOrderRequest, OrderSide, OrderType, OpenType
)

async def create_order():
    config = SDKConfig(auth_token="WEB...")
    
    async with MexcFuturesClient(config) as client:
        order = SubmitOrderRequest(
            symbol="BTC_USDT",
            price=50000.0,
            vol=0.001,
            side=OrderSide.OPEN_LONG,      # 1=long, 3=short
            type=OrderType.LIMIT,           # 1=limit, 5=market
            openType=OpenType.CROSS,        # 1=isolated, 2=cross
            leverage=10,
            stopLossPrice=49000.0,          # Опционально
            takeProfitPrice=52000.0,        # Опционально
        )
        
        response = await client.submit_order(order)
        print(f"Order ID: {response.data}")
```

#### Отмена ордеров

```python
# Отмена по ID
result = await client.cancel_order([123456789])

# Отмена по внешнему ID
from mexc_futures import CancelOrderByExternalIdRequest

result = await client.cancel_order_by_external_id(
    CancelOrderByExternalIdRequest(
        symbol="BTC_USDT",
        externalOid="my-order-123"
    )
)

# Отмена всех ордеров
from mexc_futures import CancelAllOrdersRequest

result = await client.cancel_all_orders(
    CancelAllOrdersRequest(symbol="BTC_USDT")  # Опционально
)
```

#### Получение информации об ордере

```python
# По ID ордера
order = await client.get_order(123456789)
print(f"Статус: {order.data.state}, Исполнено: {order.data.dealVol}")

# По внешнему ID
order = await client.get_order_by_external_id("BTC_USDT", "my-order-123")
```

#### История ордеров

```python
from mexc_futures import OrderHistoryParams

params = OrderHistoryParams(
    category=1,
    page_num=1,
    page_size=20,
    states=3,  # 3 = completed
    symbol="BTC_USDT"
)

history = await client.get_order_history(params)
for order in history.data.orders:
    print(f"{order.id}: {order.side} {order.vol} @ {order.price}")
```

### Аккаунт и позиции

#### Баланс аккаунта

```python
asset = await client.get_account_asset("USDT")
print(f"Баланс: {asset.data.cashBalance}")
print(f"Доступно: {asset.data.availableBalance}")
print(f"Нереализованная PnL: {asset.data.unrealized}")
```

#### Открытые позиции

```python
# Все позиции
positions = await client.get_open_positions()

# По конкретному символу
positions = await client.get_open_positions("BTC_USDT")

for pos in positions.data:
    print(f"{pos.symbol}: {pos.holdVol} @ {pos.holdAvgPrice}")
    print(f"  PnL: {pos.realised}, Leverage: {pos.leverage}x")
```

#### История позиций

```python
from mexc_futures import PositionHistoryParams

params = PositionHistoryParams(
    symbol="BTC_USDT",
    type=1,  # 1=long, 2=short
    page_num=1,
    page_size=20
)

history = await client.get_position_history(params)
```

#### Комиссии и лимиты

```python
# Комиссии
fees = await client.get_fee_rate()
for fee in fees.data:
    print(f"{fee.symbol}: maker={fee.makerFeeRate}, taker={fee.takerFeeRate}")

# Лимиты риска
limits = await client.get_risk_limit()
for limit in limits.data:
    print(f"{limit.symbol}: max leverage={limit.maxLeverage}x")
```

### Рыночные данные

#### Тикер

```python
ticker = await client.get_ticker("BTC_USDT")
print(f"Цена: {ticker.data.lastPrice}")
print(f"24h объём: {ticker.data.volume24}")
print(f"Funding rate: {ticker.data.fundingRate}")
```

#### Информация о контракте

```python
# Один контракт
detail = await client.get_contract_detail("BTC_USDT")

# Все контракты
all_contracts = await client.get_contract_detail()
```

#### Стакан (Order Book)

```python
depth = await client.get_contract_depth("BTC_USDT", limit=20)
book = depth.get_depth()

print("Asks (продажа):")
for ask in book.asks[:5]:
    print(f"  {ask.price}: {ask.volume}")

print("Bids (покупка):")
for bid in book.bids[:5]:
    print(f"  {bid.price}: {bid.volume}")
```

## WebSocket API

### Подключение и подписки

```python
import asyncio
from mexc_futures import MexcFuturesWebSocket, WebSocketConfig

async def main():
    config = WebSocketConfig(
        api_key="mx0...",
        secret_key="..."
    )
    
    ws = MexcFuturesWebSocket(config)
    
    # Регистрация обработчиков через декоратор
    @ws.on("ticker")
    async def on_ticker(data):
        print(f"Цена: {data['lastPrice']}")
    
    @ws.on("order_update")
    async def on_order(data):
        print(f"Ордер обновлён: {data}")
    
    async with ws:
        # Подписка на публичные данные
        await ws.subscribe_to_ticker("BTC_USDT")
        
        # Логин для приватных данных
        await ws.login()
        await asyncio.sleep(1)  # Дождаться логина
        
        # Подписка на приватные данные
        await ws.subscribe_to_orders(["BTC_USDT"])
        
        # Слушать 60 секунд
        await asyncio.sleep(60)

asyncio.run(main())
```

### Публичные каналы

```python
# Тикер одного символа
await ws.subscribe_to_ticker("BTC_USDT")
await ws.unsubscribe_from_ticker("BTC_USDT")

# Все тикеры
await ws.subscribe_to_all_tickers()
await ws.unsubscribe_from_all_tickers()

# Сделки
await ws.subscribe_to_deals("BTC_USDT")
await ws.unsubscribe_from_deals("BTC_USDT")

# Стакан (инкрементальный)
await ws.subscribe_to_depth("BTC_USDT")
await ws.unsubscribe_from_depth("BTC_USDT")

# Стакан (полный снапшот)
await ws.subscribe_to_full_depth("BTC_USDT", limit=20)  # 5, 10 или 20

# Свечи
await ws.subscribe_to_kline("BTC_USDT", "Min1")  # Min1, Min5, Hour1, Day1...
await ws.unsubscribe_from_kline("BTC_USDT")

# Funding rate
await ws.subscribe_to_funding_rate("BTC_USDT")

# Index price
await ws.subscribe_to_index_price("BTC_USDT")

# Fair price
await ws.subscribe_to_fair_price("BTC_USDT")
```

### Приватные каналы

После вызова `login()`:

```python
# Обновления ордеров
await ws.subscribe_to_orders(["BTC_USDT", "ETH_USDT"])

# Исполнения ордеров
await ws.subscribe_to_order_deals()

# Обновления позиций
await ws.subscribe_to_positions()

# Изменения баланса
await ws.subscribe_to_assets()

# ADL уровни
await ws.subscribe_to_adl_levels()

# Все приватные данные
await ws.subscribe_to_all_private()
```

### События WebSocket

| Событие | Описание |
|---------|----------|
| `connected` | Подключение установлено |
| `disconnected` | Соединение закрыто |
| `login` | Успешный логин |
| `login_failed` | Ошибка логина |
| `subscribed` | Подписка подтверждена |
| `error` | Ошибка |
| `ticker` | Обновление тикера |
| `tickers` | Все тикеры |
| `deal` | Сделки |
| `depth` | Стакан |
| `kline` | Свечи |
| `funding_rate` | Funding rate |
| `order_update` | Обновление ордера |
| `order_deal` | Исполнение ордера |
| `position_update` | Обновление позиции |
| `asset_update` | Изменение баланса |

## Обработка ошибок

```python
from mexc_futures import (
    MexcFuturesError,
    MexcAuthenticationError,
    MexcApiError,
    MexcNetworkError,
    MexcValidationError,
    MexcRateLimitError,
)

try:
    await client.submit_order(order)
except MexcAuthenticationError as e:
    print(f"Ошибка авторизации: {e.user_friendly_message}")
except MexcValidationError as e:
    print(f"Ошибка валидации поля '{e.field}': {e.message}")
except MexcRateLimitError as e:
    print(f"Превышен лимит запросов. Повторите через {e.retry_after}с")
except MexcApiError as e:
    print(f"API ошибка {e.status_code}: {e.user_friendly_message}")
except MexcNetworkError as e:
    print(f"Сетевая ошибка: {e.message}")
except MexcFuturesError as e:
    print(f"Общая ошибка: {e.message}")
```

### Логирование ошибок

```python
from mexc_futures import format_error_for_logging

try:
    await client.submit_order(order)
except MexcFuturesError as e:
    # Подробный вывод для логов
    print(format_error_for_logging(e))
```

## Типы ордеров

### OrderSide (направление)

| Значение | Описание |
|----------|----------|
| `OPEN_LONG` (1) | Открыть лонг |
| `CLOSE_SHORT` (2) | Закрыть шорт |
| `OPEN_SHORT` (3) | Открыть шорт |
| `CLOSE_LONG` (4) | Закрыть лонг |

### OrderType (тип)

| Значение | Описание |
|----------|----------|
| `LIMIT` (1) | Лимитный ордер |
| `POST_ONLY` (2) | Только maker |
| `IOC` (3) | Immediate or Cancel |
| `FOK` (4) | Fill or Kill |
| `MARKET` (5) | Рыночный ордер |
| `MARKET_TO_LIMIT` (6) | Рыночный → лимитный |

### OpenType (тип маржи)

| Значение | Описание |
|----------|----------|
| `ISOLATED` (1) | Изолированная маржа |
| `CROSS` (2) | Кросс-маржа |

## Интервалы свечей

- `Min1`, `Min5`, `Min15`, `Min30`, `Min60`
- `Hour4`, `Hour8`
- `Day1`, `Week1`, `Month1`

## Лицензия

MIT
