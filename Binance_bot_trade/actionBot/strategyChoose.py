 
from Binance_bot_trade.config import botConfig
import Binance_bot_trade.config.strategyConfig as strategyConfig
import Binance_bot_trade.analysis.snip_spot as snip_spot
import Binance_bot_trade.analysis.snip_futures as snip_futures
import csv
from datetime import datetime
import csv
import pandas as pd
from datetime import datetime
import Binance_bot_trade.analysis.update_price as update_price

 

def save_strategy_history(trade_mode, selected_strategies, ohlcv_data, rsi_data, macd_data, atr_data):
    filename = "./Binance_bot_trade/logs/strategy_history.csv"
    fieldnames = ["timestamp", "trade_mode", "strategies", "close_price", "RSI", "MACD", "ATR", "profit_percent"]

    # Lấy giá hiện tại từ update_price.py
    prices = update_price.update_prices()
    current_price = prices["spot"]["spot_price"] if trade_mode == "SPOT" else prices["futures"]["futures_price"]

    # Lấy giá kích hoạt chiến lược
    entry_price = ohlcv_data[-1]["close"]

    # Tính lợi nhuận của chiến lược
    profit_percent = ((current_price - entry_price) / entry_price) * 100 if current_price else None

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trade_mode": trade_mode,
        "strategies": ", ".join(selected_strategies),
        "close_price": entry_price,
        "RSI": rsi_data[-1]["rsi"],
        "MACD": macd_data[-1]["macd"],
        "ATR": atr_data[-1]["atr"],
        "profit_percent": profit_percent
    }

    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:  # Nếu file rỗng, ghi tiêu đề
            writer.writeheader()
        writer.writerow(data)

    print(f"📊 Chiến lược đã được lưu vào {filename} với lợi nhuận {profit_percent:.2f}%")

def choose_strategies(trade_mode):
    active_strategy = botConfig.ACTIVE_STRATEGY
    available_strategies = set(strategyConfig.get_strategies_by_field(trade_mode))

    print(f"\n🔍 Đang phân tích thị trường để chọn chiến lược phù hợp cho {trade_mode}...")

    if trade_mode == "SPOT":
        pair = botConfig.TRADE_PAIRS["SPOT"][0]
        ohlcv_data = snip_spot.get_ohlcv(pair)
    else:
        pair = botConfig.TRADE_PAIRS["FUTURES"][0]
        ohlcv_data = snip_futures.get_futures_ohlcv(pair)

    # 📌 Dữ liệu kỹ thuật
    rsi_data = snip_spot.calculate_rsi(ohlcv_data, 14) if trade_mode == "SPOT" else snip_futures.calculate_rsi(ohlcv_data, 14)
    macd_data = snip_spot.calculate_macd(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_macd(ohlcv_data)
    atr_data = snip_spot.calculate_atr(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_atr(ohlcv_data)

    ichimoku_data = snip_spot.calculate_ichimoku(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_ichimoku(ohlcv_data)
    golden_cross_data = snip_spot.calculate_golden_cross(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_golden_cross(ohlcv_data)
    vwap_data = snip_spot.calculate_vwap(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_vwap(ohlcv_data)
    pivot_data = snip_spot.calculate_pivot_points(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_pivot_points(ohlcv_data)

    volume_profile_data = snip_spot.calculate_volume_profile(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_volume_profile(ohlcv_data)
    bollinger_bands = snip_spot.calculate_bollinger_bands(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_bollinger_bands(ohlcv_data)
    mean_reversion_signal = snip_spot.check_mean_reversion(ohlcv_data, bollinger_bands) if trade_mode == "SPOT" else snip_futures.check_mean_reversion(ohlcv_data, bollinger_bands)

    # 📌 Chỉ dành cho Futures
    if trade_mode == "FUTURES":
        funding_rate = snip_futures.get_funding_rate(pair)
        open_interest = snip_futures.get_open_interest(pair)
        grid_trading_signal = snip_futures.check_grid_trading(ohlcv_data, rsi_data, atr_data)
        market_making_signal = snip_futures.check_market_making(open_interest)

    print(f"\n📊 Dữ liệu thị trường ({trade_mode}):")
    print(f"🔹 RSI: {rsi_data[-1]['rsi']}")
    print(f"🔹 MACD: {macd_data[-1]['macd']} - Signal: {macd_data[-1]['signal']}")
    print(f"🔹 ATR: {atr_data[-1]['atr']}")

    if trade_mode == "FUTURES":
        print(f"🔹 Funding Rate: {funding_rate['funding_rate']}")
        print(f"🔹 Open Interest: {open_interest['open_interest']}")

    selected_strategies = set()

    # 🔥 Chiến lược dựa trên RSI
    if rsi_data[-1]["rsi"] < 30:
        selected_strategies.add("MEAN_REVERSION")
        selected_strategies.add("BOLLINGER_BANDS")
    if mean_reversion_signal and "MEAN_REVERSION" in available_strategies:
        print("🔹 Mean Reversion được kích hoạt do giá chạm Bollinger Bands.")
        selected_strategies.add("MEAN_REVERSION")
    if rsi_data[-1]["rsi"] > 70:
        selected_strategies.add("BREAKOUT")
        selected_strategies.add("SCALPING")
    # Nếu RSI trên 70, thêm Mean Reversion
    if rsi_data[-1]["rsi"] > 70:
        print("🔹 RSI trên 70, kích hoạt MEAN_REVERSION!")
        selected_strategies.add("MEAN_REVERSION")

    # 🔥 Chiến lược dựa trên MACD
    if macd_data[-1]["macd"] - macd_data[-1]["signal"] > 50:
        selected_strategies.add("BREAKOUT")

    if macd_data[-1]["macd"] - macd_data[-1]["signal"] > 10:
        selected_strategies.add("RSI_MACD")

    # 🔥 ATR cao → Grid Trading & Scalping
    if atr_data[-1]["atr"] > atr_data[-10]["atr"] * 1.5:
        selected_strategies.add("GRID_TRADING")
        selected_strategies.add("SCALPING")
    atr_avg_50 = sum([atr["atr"] for atr in atr_data[-50:]]) / 50 if len(atr_data) >= 50 else atr_data[-1]["atr"]
    if atr_data[-1]["atr"] > atr_avg_50 * 1.3 and 40 < rsi_data[-1]["rsi"] < 60 and abs(macd_data[-1]["macd"] - macd_data[-1]["signal"]) < 10:
        print("🔹 ATR cao, RSI trung lập, MACD không có xu hướng rõ ràng -> kích hoạt GRID_TRADING!")
        selected_strategies.add("GRID_TRADING")
 

    # 🔥 Volume Profile: Nếu giá gần vùng có volume cao nhất
    # Nếu giá gần đỉnh khối lượng nhưng xu hướng yếu, tránh giao dịch Breakout
    if abs(ohlcv_data[-1]["close"] - volume_profile_data["max_volume_price"]) / volume_profile_data["max_volume_price"] < 0.01:
        if macd_data[-1]["macd"] - macd_data[-1]["signal"] < 10:  # Xu hướng yếu
            print("🔹 Giá gần vùng Volume Profile nhưng MACD yếu, tránh Breakout!")
        else:
            selected_strategies.add("VOLUME_PROFILE")


    # 🔥 Ichimoku Cloud nếu giá cao hơn Senkou Span A
    if ohlcv_data[-1]["close"] > ichimoku_data["senkou_span_a"]:
        selected_strategies.add("ICHIMOKU")

    # 🔥 Golden Cross nếu EMA 50 > EMA 200
    if golden_cross_data["golden_cross"]:
        selected_strategies.add("GOLDEN_CROSS")

    # 🔥 VWAP nếu giá vượt qua VWAP
    if ohlcv_data[-1]["close"] > vwap_data["vwap"]:
        selected_strategies.add("VWAP")
        vwap_avg_volume = sum([ohlcv["volume"] for ohlcv in ohlcv_data[-20:]]) / 20
    if ohlcv_data[-1]["close"] > vwap_data["vwap"]:
        if ohlcv_data[-1]["volume"] > 1.5 * vwap_avg_volume:
            print("🔹 Giá trên VWAP và khối lượng cao -> Kích hoạt VWAP!")
            selected_strategies.add("VWAP")
        else:
            print("⚠️ Giá trên VWAP nhưng khối lượng thấp, tránh giao dịch.")

    # 🔥 Pivot Points nếu giá gần mức hỗ trợ hoặc kháng cự
    # Nếu giá gần mức hỗ trợ hoặc kháng cự và ATR thấp -> Mean Reversion
    if abs(ohlcv_data[-1]["close"] - pivot_data["resistance_1"]) / pivot_data["resistance_1"] < 0.01 or \
    abs(ohlcv_data[-1]["close"] - pivot_data["support_1"]) / pivot_data["support_1"] < 0.01:
        if atr_data[-1]["atr"] < atr_avg_50:  # ATR thấp -> Xu hướng yếu -> Mean Reversion
            print("🔹 Giá gần hỗ trợ/kháng cự và ATR thấp, kích hoạt MEAN_REVERSION!")
            selected_strategies.add("MEAN_REVERSION")
        else:
            selected_strategies.add("PIVOT_POINTS")

    adx_data = snip_futures.calculate_adx(ohlcv_data) if trade_mode == "FUTURES" else snip_spot.calculate_adx(ohlcv_data)
    price_change_pct = abs(ohlcv_data[-1]["close"] - ohlcv_data[-10]["close"]) / ohlcv_data[-10]["close"] * 100
    if adx_data[-1]["adx"] < 20 and price_change_pct < 3:
        print("🔹 ADX thấp & giá biến động nhỏ -> Kích hoạt GRID_TRADING!")
        selected_strategies.add("GRID_TRADING")
    else:
        print("⚠️ Thị trường có xu hướng hoặc biến động mạnh, tránh GRID_TRADING!")

    if adx_data[-1]["adx"] < 20:
        print("🔹 ADX thấp (<20), thị trường yếu -> Ưu tiên Mean Reversion & Grid Trading.")
        selected_strategies.add("MEAN_REVERSION")
        selected_strategies.add("GRID_TRADING")
    elif adx_data[-1]["adx"] > 30:
        print("🔹 ADX cao (>30), xu hướng mạnh -> Kích hoạt Breakout & Trend-following!")
        selected_strategies.add("BREAKOUT")
        selected_strategies.add("ICHIMOKU")
    # 🔥 Chỉ dành cho Futures
    if trade_mode == "FUTURES":
        print(f"🔹 Funding Rate: {funding_rate['funding_rate']}")
        
        # 🔥 1. Kiểm tra Funding Rate
        if funding_rate["funding_rate"] > botConfig.FUNDING_RATE_THRESHOLD:
            print(f"⚠️ Funding Rate cao ({funding_rate['funding_rate']}), tránh giao dịch!")
            return []
        if funding_rate["funding_rate"] < 0 and bid_ask_spread < 0.02:
            print("🔹 Funding Rate âm và Spread thấp -> Kích hoạt MARKET_MAKING!")
            selected_strategies.add("MARKET_MAKING")
        elif funding_rate["funding_rate"] > 0.01:
            print("⚠️ Funding Rate cao, tránh Market Making!")


        # 🔥 2. Lấy dữ liệu Open Interest (có thể trả về None)
        open_interest_data = snip_futures.get_open_interest(pair)
        open_interest_value = open_interest_data.get("open_interest", None) if open_interest_data else None

        # 🔥 3. Kiểm tra Open Interest chỉ khi có dữ liệu hợp lệ
        if open_interest_value is not None:
            print(f"🔹 Open Interest hiện tại: {open_interest_value}")

            if open_interest_value > botConfig.OPEN_INTEREST_THRESHOLD:
                bid_ask_spread = snip_futures.get_bid_ask_spread(pair)
                if bid_ask_spread < 0.02 and atr_data[-1]["atr"] < atr_avg_50:  # ATR thấp → Thị trường ít biến động
                    print("🔹 Open Interest cao, Spread thấp và ATR thấp -> kích hoạt MARKET_MAKING!")
                    selected_strategies.add("MARKET_MAKING")

        # 🔥 4. Kích hoạt Grid Trading nếu ATR cao nhưng thị trường không có xu hướng mạnh
        if atr_data[-1]["atr"] > atr_avg_50 * 1.3 and 40 < rsi_data[-1]["rsi"] < 60 and abs(macd_data[-1]["macd"] - macd_data[-1]["signal"]) < 10:
            print("🔹 ATR cao, RSI trung lập, MACD không có xu hướng rõ ràng -> kích hoạt GRID_TRADING!")
            selected_strategies.add("GRID_TRADING")

        # 🔥 5. Kích hoạt chiến lược dựa trên tín hiệu thuật toán
        if market_making_signal:
            selected_strategies.add("MARKET_MAKING")

        if grid_trading_signal:
            selected_strategies.add("GRID_TRADING")


    if not selected_strategies:
        selected_strategies.add(active_strategy)

    print(f"✅ Chiến lược được chọn ({trade_mode}): {list(selected_strategies)}")
        # 🔥 Gọi hàm lưu lịch sử chiến lược
    save_strategy_history(trade_mode, list(selected_strategies), ohlcv_data, rsi_data, macd_data, atr_data)
    chosen_strategies = list(selected_strategies)
    if isinstance(chosen_strategies, list):
        chosen_strategies = {"SPOT": chosen_strategies if trade_mode in ["SPOT", "BOTH"] else [],
                            "FUTURES": chosen_strategies if trade_mode in ["FUTURES", "BOTH"] else []}

    return chosen_strategies
def tech_data_spot(trade_mode):
    if trade_mode == "SPOT":
        pair = botConfig.TRADE_PAIRS["SPOT"][0]
        ohlcv_data = snip_spot.get_ohlcv(pair)
    else:
        pair = botConfig.TRADE_PAIRS["FUTURES"][0]
        ohlcv_data = snip_futures.get_futures_ohlcv(pair)

    # 📌 Dữ liệu kỹ thuật
    rsi_data = snip_spot.calculate_rsi(ohlcv_data, 14) if trade_mode == "SPOT" else snip_futures.calculate_rsi(ohlcv_data, 14)
    macd_data = snip_spot.calculate_macd(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_macd(ohlcv_data)
    atr_data = snip_spot.calculate_atr(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_atr(ohlcv_data)

    ichimoku_data = snip_spot.calculate_ichimoku(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_ichimoku(ohlcv_data)
    golden_cross_data = snip_spot.calculate_golden_cross(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_golden_cross(ohlcv_data)
    vwap_data = snip_spot.calculate_vwap(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_vwap(ohlcv_data)
    pivot_data = snip_spot.calculate_pivot_points(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_pivot_points(ohlcv_data)

    volume_profile_data = snip_spot.calculate_volume_profile(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_volume_profile(ohlcv_data)
    bollinger_bands = snip_spot.calculate_bollinger_bands(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_bollinger_bands(ohlcv_data)
    mean_reversion_signal = snip_spot.check_mean_reversion(ohlcv_data, bollinger_bands) if trade_mode == "SPOT" else snip_futures.check_mean_reversion(ohlcv_data, bollinger_bands)
    return ohlcv_data, rsi_data, macd_data, atr_data, ichimoku_data, golden_cross_data, vwap_data, pivot_data, volume_profile_data, bollinger_bands, mean_reversion_signal

def tech_data_furtures():
    trade_mode = "FUTURES"
    pair = botConfig.TRADE_PAIRS["FUTURES"][0]
    ohlcv_data = snip_futures.get_futures_ohlcv(pair)

    # 📌 Dữ liệu kỹ thuật
    rsi_data = snip_spot.calculate_rsi(ohlcv_data, 14) if trade_mode == "SPOT" else snip_futures.calculate_rsi(ohlcv_data, 14)
    macd_data = snip_spot.calculate_macd(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_macd(ohlcv_data)
    atr_data = snip_spot.calculate_atr(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_atr(ohlcv_data)

    ichimoku_data = snip_spot.calculate_ichimoku(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_ichimoku(ohlcv_data)
    golden_cross_data = snip_spot.calculate_golden_cross(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_golden_cross(ohlcv_data)
    vwap_data = snip_spot.calculate_vwap(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_vwap(ohlcv_data)
    pivot_data = snip_spot.calculate_pivot_points(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_pivot_points(ohlcv_data)

    volume_profile_data = snip_spot.calculate_volume_profile(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_volume_profile(ohlcv_data)
    bollinger_bands = snip_spot.calculate_bollinger_bands(ohlcv_data) if trade_mode == "SPOT" else snip_futures.calculate_bollinger_bands(ohlcv_data)
    mean_reversion_signal = snip_spot.check_mean_reversion(ohlcv_data, bollinger_bands) if trade_mode == "SPOT" else snip_futures.check_mean_reversion(ohlcv_data, bollinger_bands)
    return atr_data
 
 
if __name__ == "__main__":
    chosen_strategies = {}

    if botConfig.TRADE_MODE in ["SPOT", "FUTURES"]:
        chosen_strategies[botConfig.TRADE_MODE] = choose_strategies(botConfig.TRADE_MODE)
    elif botConfig.TRADE_MODE == "BOTH":
        chosen_strategies= choose_strategies("SPOT")
        chosen_strategies  = choose_strategies("FUTURES")

    print(f"\n🚀 Bot sẽ giao dịch với các chiến lược: {chosen_strategies}")
