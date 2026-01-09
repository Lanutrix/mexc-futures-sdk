import asyncio

from mexc_futures import (
    MexcFuturesClient,
    MexcAuthenticationError,
    SDKConfig,
    SubmitOrderRequest,
    OrderSide,
    OrderType,
    OpenType,
)

# Вставьте сюда ваш токен, скопированный из браузера
MY_WEB_TOKEN = "WEBc853cd57ce18abc87667180c744cefb2881a5843bd6823fc53ffbd3550f237f8"


async def main():
    # Инициализация клиента
    config = SDKConfig(auth_token=MY_WEB_TOKEN)

    async with MexcFuturesClient(config) as client:
        try:
            print("[...] Получаем тикер BTC_USDT...")
            ticker = await client.get_ticker("BTC_USDT")

            if ticker and ticker.data:
                print(f"[OK] Цена BTC: {ticker.data.lastPrice}")
            else:
                print("[!] Данные тикера не получены")
                return

            # Получаем баланс
            print("[...] Получаем баланс...")
            assets = await client.get_account_asset("USDT")
            print(f"[$] Баланс: {assets.data}")

            # Открываем лонг позицию на BTC
            print("[...] Открываем LONG ордер на BTC_USDT...")
            
            current_price = ticker.data.lastPrice
            
            # order = SubmitOrderRequest(
            #     symbol="BTC_USDT",
            #     price=current_price,           # Текущая цена (для лимитного ордера)
            #     vol=19,                     # Минимальный объём (0.001 BTC)
            #     side=OrderSide.OPEN_LONG,      # Открыть лонг
            #     type=OrderType.MARKET,         # Рыночный ордер
            #     openType=OpenType.CROSS,       # Кросс-маржа
            #     leverage=100,                   # Плечо 100x
            # )
            
            # response = await client.submit_order(order)
            
            # if response.success:
            #     print(f"[OK] Ордер создан! Order ID: {response.data}")
            # else:
            #     print(f"[!] Ошибка создания ордера: {response.message}")

            # await asyncio.sleep(30)
            
            # Закрываем LONG позицию
            print("[...] Закрываем LONG позицию...")
            close_order = SubmitOrderRequest(
                symbol="BTC_USDT",
                price=current_price,           # Для MARKET ордера не влияет, но обязательно
                vol=19,                        # Тот же объём, что открывали
                side=OrderSide.CLOSE_LONG,     # Закрыть лонг
                type=OrderType.MARKET,         # Рыночный ордер (быстрое закрытие)
                openType=OpenType.CROSS,       # Кросс-маржа
            )
            
            result = await client.submit_order(close_order)

            if result.success:
                print(f"[OK] Позиция закрыта! Order ID: {result.data}")
            else:
                print(f"[!] Ошибка закрытия позиции: {result.message}")
        except MexcAuthenticationError:
            print("[X] Ошибка авторизации. Обновите WEB-токен.")
        except Exception as error:
            print(f"[X] Произошла ошибка: {error}")


if __name__ == "__main__":
    asyncio.run(main())

