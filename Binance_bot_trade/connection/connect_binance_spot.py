from binance.client import Client
import Binance_bot_trade.config.config as config
import os
import time

# Kết nối đến Binance Spot (Testnet)
client_spot = Client(config.API_Key_spot, config.Secret_Key_spot, tld='com', requests_params={"timeout": 30})
client_spot.API_URL = config.SPOT_TESTNET_URL  # Ghi đè API_URL cho Spot Testnet

# Hàm tự động đồng bộ thời gian nếu gặp lỗi timestamp
def handle_timestamp_error(e):
    error_message = str(e)
    if "Timestamp for this request was 1000ms ahead of the server" in error_message:
        print("🔄 Phát hiện lỗi timestamp, đang đồng bộ thời gian...")
        os.system("w32tm /resync")
        time.sleep(2)
        return True
    return False

# Kiểm tra số dư USDT trên Spot và trả về số dư
def check_spot_balance():
    print("\n📌 Kiểm tra số dư USDT trên Spot...")
    try:
        account_info = client_spot.get_account()
        for balance in account_info["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["free"])
                print(f"💰 Số dư USDT Spot: {usdt_balance}")
                return usdt_balance
        print("❌ Không tìm thấy USDT trong tài khoản Spot.")
        return 0.0
    except Exception as e:
        print(f"❌ Lỗi khi lấy số dư Spot: {e}")
        if handle_timestamp_error(e):
            return check_spot_balance()
        return 0.0

# Kiểm tra giá BTCUSDT trên Spot và trả về giá
def get_spot_price():
    print("\n📌 Giá BTCUSDT Spot:")
    try:
        ticker = client_spot.get_symbol_ticker(symbol="BTCUSDT")
        price = float(ticker["price"])
        print(f"💰 Giá hiện tại: {price} USDT")
        return price
    except Exception as e:
        print(f"❌ Lỗi khi lấy giá Spot: {e}")
        return 0.0

if __name__ == "__main__":
    spot_balance = check_spot_balance()
    spot_price = get_spot_price()
