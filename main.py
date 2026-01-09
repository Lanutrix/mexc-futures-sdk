import asyncio

from mexc_futures import MexcFuturesClient, MexcAuthenticationError, SDKConfig

# Вставьте сюда ваш токен, скопированный из браузера
MY_WEB_TOKEN = "WEB3720a184d00ad366e2ba616596183f957e55a616c0ba173218c8bfe3c1d42327"


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

            # Пример получения баланса (раскомментируйте, если токен валидный)

            print("[...] Получаем баланс...")
            assets = await client.get_account_asset("USDT")
            print(f"[$] Баланс: {assets.data}")

        except MexcAuthenticationError:
            print("[X] Ошибка авторизации. Обновите WEB-токен.")
        except Exception as error:
            print(f"[X] Произошла ошибка: {error}")


if __name__ == "__main__":
    asyncio.run(main())

