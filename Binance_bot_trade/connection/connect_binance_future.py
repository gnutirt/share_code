from binance.client import Client
import Binance_bot_trade.config.config as config
import Binance_bot_trade.config.botConfig as botConfig
import os
import time

# Kết nối đến Binance Futures Testnet

# Chọn API Key và Secret dựa trên TEST_MODE
if botConfig.TEST_MODE:
    api_key = config.API_Key_future_Test
    api_secret = config.API_Secret_future_Test
else:
    api_key = config.API_Key_future
    api_secret = config.API_Secret_future

# Khởi tạo client với API Key tương ứng
client_futures = Client(api_key, api_secret, testnet=botConfig.TEST_MODE, requests_params={"timeout": 30})
  
# Hàm tự động đồng bộ thời gian nếu gặp lỗi timestamp
def handle_timestamp_error(e):
    error_message = str(e)
    if "Timestamp for this request was 1000ms ahead of the server's time." in error_message:
        print("🔄 Phát hiện lỗi timestamp, đang đồng bộ thời gian...")
        os.system("w32tm /resync")
        time.sleep(2)
        return True
    return False

# Kiểm tra số dư USDT trên Futures và trả về số dư
def check_futures_balance():
    print("\n📌 Kiểm tra số dư USDT trên Futures...")
    try:
        account_info = client_futures.futures_account_balance()
        for balance in account_info:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["balance"])
                print(f"💰 Số dư USDT Futures: {usdt_balance}")
                return usdt_balance
        print("❌ Không tìm thấy USDT trong tài khoản Futures.")
        return 0.0
    except Exception as e:
        print(f"❌ Lỗi khi lấy số dư Futures: {e}")
        if handle_timestamp_error(e):
            return check_futures_balance()
        return 0.0

# Kiểm tra giá BTCUSDT trên Futures và trả về giá
def get_futures_price():
    print("\n📌 Giá BTCUSDT Futures:")
    try:
        ticker = client_futures.futures_symbol_ticker(symbol="BTCUSDT")
        price = float(ticker["price"])
        print(f"💰 Giá hiện tại: {price} USDT")
        return price
    except Exception as e:
        print(f"❌ Lỗi khi lấy giá Futures: {e}")
        return 0.0

if __name__ == "__main__":
    futures_balance = check_futures_balance()
    futures_price = get_futures_price()
