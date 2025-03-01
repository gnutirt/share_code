import logging
import Binance_bot_trade.connection.connect_binance_spot as connect_binance_spot
import Binance_bot_trade.connection.connect_binance_future as connect_binance_future
import Binance_bot_trade.config.config as config

client_spot = connect_binance_spot.client_spot  # Kết nối Spot
client_futures = connect_binance_future.client_futures  # Kết nối Futures

# 🔥 Lấy giá Spot hiện tại và trả về giá trị
def get_spot_price(symbol=config.TRADE_PAIR_SPOT_BTCUSDT):
    try:
        ticker = client_spot.get_symbol_ticker(symbol=symbol)
        price = float(ticker["price"])
        return {"symbol": symbol, "spot_price": price}
    except Exception as e:
        return {"symbol": symbol, "spot_price": None, "error": str(e)}

# 🔥 Lấy giá Futures hiện tại và trả về giá trị
def get_futures_price(symbol=config.TRADE_PAIR_FUTURES_BTCUSDT):
    try:
        ticker = client_futures.futures_ticker(symbol=symbol)  # Dùng API lấy cả previous_close
        price = float(ticker["lastPrice"])
        previous_close = float(ticker.get("prevClosePrice", price))  # Nếu không có, lấy chính giá hiện tại
        
        return {
            "symbol": symbol,
            "futures_price": price,
            "previous_close": previous_close
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "futures_price": None,
            "previous_close": None,
            "error": str(e)
        }

# 🔥 Hàm cập nhật cả giá Spot và Futures
def update_prices():
    spot_info = get_spot_price()
    futures_info = get_futures_price()

    return {
        "spot": spot_info,
        "futures": futures_info
    }
def get_order_book(symbol, limit=10):
    """
    Lấy dữ liệu Order Book từ Binance Futures.
    
    :param symbol: Cặp giao dịch (VD: BTCUSDT)
    :param limit: Số mức giá bid/ask muốn lấy
    :return: Dictionary chứa danh sách bid và ask
    """
    try:
        order_book = client_futures.futures_order_book(symbol=symbol, limit=limit)
        return {
            "bids": order_book["bids"],  # Danh sách giá đặt mua
            "asks": order_book["asks"]   # Danh sách giá đặt bán
        }
    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy Order Book cho {symbol}: {e}")
        return None
def get_btc_24h_change():
    """Lấy phần trăm thay đổi giá BTC trong 24 giờ"""
    try:
        ticker_24h = client_futures.futures_ticker(symbol="BTCUSDT")
        price_change_percent = float(ticker_24h["priceChangePercent"])
        return price_change_percent
    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy biến động BTC 24h: {e}")
        return None
# Trong Binance_bot_trade/analysis/update_price.py
import requests

def get_funding_rate(symbol):
    """
    Lấy Funding Rate hiện tại cho symbol từ Binance Futures API bằng HTTP GET.
    :param symbol: Cặp giao dịch (e.g., "BTCUSDT")
    :return: Funding Rate (float), hoặc None nếu lỗi hoặc symbol không tìm thấy
    """
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        data = response.json()  # Chuyển đổi JSON thành danh sách Python
        
        # Tìm symbol trong danh sách
        for item in data:
            if item["symbol"] == symbol:
                funding_rate = float(item["lastFundingRate"])
                return funding_rate
        
        logging.warning(f"⚠️ Không tìm thấy Funding Rate cho {symbol} trong dữ liệu API!")
        return None
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Lỗi khi gọi API Funding Rate: {e}")
        return None
    except ValueError as e:
        logging.error(f"❌ Lỗi khi phân tích JSON Funding Rate: {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Lỗi không xác định khi lấy Funding Rate cho {symbol}: {e}")
        return None
if __name__ == "__main__":
    symbol = config.TRADE_PAIR_FUTURES_BTCUSDT
    get_funding_rate = get_funding_rate(symbol)
    print(get_funding_rate)