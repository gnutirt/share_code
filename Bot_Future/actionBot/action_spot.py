import Binance_bot_trade.connection.connect_binance_spot as connect_binance_spot
import Binance_bot_trade.config.config as config
import Binance_bot_trade.config.botConfig as botConfig
import Binance_bot_trade.analysis.check_trade_history_spot as check_trade_history_spot  
import Binance_bot_trade.analysis.update_price as update_price
from Binance_bot_trade.utils import logger
import logging
client_spot = connect_binance_spot.client_spot  # Sử dụng client_spot từ file kết nối

 
# 🔥 1. Đặt lệnh Market Buy (Mua ngay với giá thị trường) sau khi kiểm tra số dư USDT
# 🔥 1. Đặt lệnh Market Buy (Mua ngay với giá thị trường)
def place_market_buy_spot(symbol, quantity):
    print(f"\n📌 Đặt lệnh Market Buy Spot cho {symbol} - Số lượng: {quantity}")

    usdt_balance = get_spot_balance("USDT")  # Kiểm tra số dư USDT
    spot_price_info = update_price.get_spot_price(symbol)  # Lấy giá Spot từ update_price.py
    spot_price = spot_price_info["spot_price"]
    
    if spot_price is None:
        print(f"❌ Lỗi khi lấy giá {symbol}, không thể đặt lệnh!")
        return None

    required_amount = quantity * spot_price  # Số USDT cần thiết để mua

    if usdt_balance < required_amount:
        print(f"❌ Không đủ USDT! Cần {required_amount:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    try:
        order = client_spot.order_market_buy(symbol=symbol, quantity=quantity)
        print(f"✅ Lệnh Market Buy thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi đặt lệnh Market Buy: {e}")
        return None

# 🔥 1. Kiểm tra số lượng lệnh đang mở
def get_open_order_count(symbol):
    """
    Lấy số lượng lệnh đang mở cho một cặp giao dịch Spot.
    
    :param symbol: Cặp giao dịch cần kiểm tra (VD: BTCUSDT)
    :return: Số lượng lệnh đang mở
    """
    try:
        open_orders = client_spot.get_open_orders(symbol=symbol)
        order_count = len(open_orders)
        print(f"📌 Số lệnh đang mở cho {symbol}: {order_count}")
        return order_count
    except Exception as e:
        print(f"❌ Lỗi khi lấy số lệnh đang mở cho {symbol}: {e}")
        return 0  # Trả về 0 nếu có lỗi
# 🔥 2. Lấy danh sách các giao dịch đang tiến hành
def get_active_trades():
    """
    Lấy danh sách các giao dịch Spot đang mở (các lệnh chưa khớp).
    
    :return: Danh sách các giao dịch đang tiến hành (list)
    """
    try:
        active_trades = []

        for symbol in botConfig.TRADE_PAIRS["SPOT"]:
            open_orders = client_spot.get_open_orders(symbol=symbol)  # Lấy danh sách lệnh mở
            if open_orders:
                for order in open_orders:
                    active_trades.append({
                        "symbol": symbol,
                        "orderId": order["orderId"],
                        "price": order["price"],
                        "quantity": order["origQty"],
                        "side": order["side"],
                        "status": order["status"]
                    })

        logging.info(f"📊 Giao dịch Spot đang tiến hành: {active_trades}")
        return active_trades

    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy danh sách giao dịch đang tiến hành: {e}")
        return []

# 🔥 2. Đặt lệnh Market Sell (Bán ngay với giá thị trường)
def place_market_sell_spot(symbol, quantity):
    print(f"\n📌 Đặt lệnh Market Sell Spot cho {symbol} - Số lượng: {quantity}")

    coin_symbol = symbol.replace("USDT", "")  # Lấy ký hiệu coin (BTC, ETH, ...)
    coin_balance = get_spot_balance(coin_symbol)  # Kiểm tra số dư coin

    if coin_balance < quantity:
        print(f"❌ Không đủ {coin_symbol}! Cần {quantity:.6f} {coin_symbol} nhưng chỉ có {coin_balance:.6f}.")
        return None  # Không thực hiện lệnh

    try:
        order = client_spot.order_market_sell(symbol=symbol, quantity=quantity)
        print(f"✅ Lệnh Market Sell thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi đặt lệnh Market Sell: {e}")
        return None


# 🔥 3. Đặt lệnh Limit Buy (Mua ở giá cố định)
def place_limit_buy_spot(symbol, price, quantity):
    print(f"\n📌 Đặt lệnh Limit Buy Spot cho {symbol} - Giá: {price}, Số lượng: {quantity}")
    try:
        order = client_spot.order_limit_buy(symbol=symbol, price=str(price), quantity=quantity, timeInForce="GTC")
        print(f"✅ Lệnh Limit Buy thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi đặt lệnh Limit Buy: {e}")
        return None

# 🔥 4. Đặt lệnh Limit Sell (Bán ở giá cố định)
def place_limit_sell_spot(symbol, price, quantity):
    print(f"\n📌 Đặt lệnh Limit Sell Spot cho {symbol} - Giá: {price}, Số lượng: {quantity}")
    try:
        order = client_spot.order_limit_sell(symbol=symbol, price=str(price), quantity=quantity, timeInForce="GTC")
        print(f"✅ Lệnh Limit Sell thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi đặt lệnh Limit Sell: {e}")
        return None

# 🔥 5. Hủy một lệnh đang chờ
def cancel_order_spot(symbol, order_id):
    print(f"\n📌 Hủy lệnh Spot - Symbol: {symbol}, Order ID: {order_id}")
    try:
        response = client_spot.cancel_order(symbol=symbol, orderId=order_id)
        print(f"✅ Lệnh đã hủy thành công!")
        return response
    except Exception as e:
        print(f"❌ Lỗi khi hủy lệnh Spot: {e}")
        return None

# 🔥 6. Kiểm tra trạng thái một lệnh
def get_order_status_spot(symbol, order_id):
    print(f"\n📌 Kiểm tra trạng thái lệnh Spot - Symbol: {symbol}, Order ID: {order_id}")
    try:
        order = client_spot.get_order(symbol=symbol, orderId=order_id)
        print(f"🔹 Trạng thái: {order['status']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra trạng thái lệnh Spot: {e}")
        return None

# 🔥 7. Kiểm tra số dư USDT trên Spot
def get_spot_balance(asset="USDT"):
    print(f"\n📌 Kiểm tra số dư {asset} trên Spot...")
    try:
        account_info = client_spot.get_account()
        for balance in account_info["balances"]:
            if balance["asset"] == asset:
                usdt_balance = float(balance["free"])
                print(f"💰 Số dư {asset} Spot: {usdt_balance}")
                return usdt_balance
        print(f"❌ Không tìm thấy {asset} trong tài khoản Spot.")
        return 0.0
    except Exception as e:
        print(f"❌ Lỗi khi lấy số dư Spot: {e}")
        return 0.0

# 🔥 8. Lấy lịch sử giao dịch Spot
 
if __name__ == "__main__":
    # Ví dụ test các hàm
    symbol = config.TRADE_PAIR_SPOT_BTCUSDT
    quantity = 0.001  # Ví dụ mua 0.001 BTC
    price = 30000  # Ví dụ giá mua bán Limit

    # Đặt lệnh market buy
    place_market_buy_spot(symbol, quantity)

    # Đặt lệnh market sell
    place_market_sell_spot(symbol, quantity)

    # Đặt lệnh limit buy
    place_limit_buy_spot(symbol, price, quantity)

    # Đặt lệnh limit sell
    place_limit_sell_spot(symbol, price + 500, quantity)  # Bán giá cao hơn

    # Kiểm tra số dư USDT
    get_spot_balance("USDT")

    # Lấy lịch sử giao dịch bằng `check_trade_history_spot.py`
    symbol = config.TRADE_PAIR_SPOT_BTCUSDT
    trade_history = check_trade_history_spot.check_trade_history_spot(symbol, limit=20)

    print(f"\n🔹 Lịch sử giao dịch Spot ({symbol}):")
    for trade in trade_history:
        print(f"🔹 ID: {trade['id']} | Giá: {trade['price']} | Số lượng: {trade['qty']} | "
              f"Loại: {trade['side']} | Thời gian: {trade['time']}")
 

    

