import Binance_bot_trade.connection.connect_binance_spot as connect_binance_spot
import Binance_bot_trade.config.config as config
import numpy as np

client_spot = connect_binance_spot.client_spot  # Kết nối Binance Spot

# 🔥 1. Lấy dữ liệu giá & volume (OHLCV)
def get_ohlcv(symbol=config.TRADE_PAIR_SPOT_BTCUSDT, interval="1h", limit=100):
    try:
        klines = client_spot.get_klines(symbol=symbol, interval=interval, limit=limit)
        ohlcv = [
            {
                "time": kline[0],
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5])
            }
            for kline in klines
        ]
        return ohlcv
    except Exception as e:
        return {"error": str(e)}

# 🔥 2. Tính SMA (Trung bình động đơn giản)
def calculate_sma(ohlcv, period=14):
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính SMA."}
    
    close_prices = np.array([candle["close"] for candle in ohlcv])
    sma_values = np.convolve(close_prices, np.ones(period)/period, mode="valid")

    return [{"time": ohlcv[i + period - 1]["time"], "sma": float(sma_values[i])} for i in range(len(sma_values))]

# 🔥 3. Tính EMA (Trung bình động lũy thừa)
def calculate_ema(ohlcv, period=14):
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính EMA."}
    
    close_prices = np.array([candle["close"] for candle in ohlcv])
    ema_values = np.zeros_like(close_prices, dtype=float)
    multiplier = 2 / (period + 1)

    ema_values[period-1] = np.mean(close_prices[:period])
    for i in range(period, len(close_prices)):
        ema_values[i] = (close_prices[i] - ema_values[i-1]) * multiplier + ema_values[i-1]

    return [{"time": ohlcv[i]["time"], "ema": float(ema_values[i])} for i in range(period-1, len(ohlcv))]

# 🔥 4. Tính RSI (Chỉ số sức mạnh tương đối)
def calculate_rsi(ohlcv, period=14):
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính RSI."}

    close_prices = np.array([candle["close"] for candle in ohlcv])
    deltas = np.diff(close_prices)
    gain = np.maximum(deltas, 0)
    loss = np.abs(np.minimum(deltas, 0))

    avg_gain = np.convolve(gain, np.ones(period)/period, mode="valid")
    avg_loss = np.convolve(loss, np.ones(period)/period, mode="valid")

    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))

    return [{"time": ohlcv[i + period]["time"], "rsi": float(rsi_values[i])} for i in range(len(rsi_values))]

# 🔥 5. Tính MACD (Chỉ báo động lượng)
def calculate_macd(ohlcv, short_period=12, long_period=26, signal_period=9):
    ema_short = calculate_ema(ohlcv, short_period)
    ema_long = calculate_ema(ohlcv, long_period)

    if isinstance(ema_short, dict) or isinstance(ema_long, dict):
        return {"error": "Không đủ dữ liệu để tính MACD."}

    min_length = min(len(ema_short), len(ema_long))
    ema_short = ema_short[-min_length:]
    ema_long = ema_long[-min_length:]

    macd_line = np.array([ema_short[i]["ema"] - ema_long[i]["ema"] for i in range(min_length)], dtype=float)
    
    if len(macd_line) < signal_period:
        return {"error": "Không đủ dữ liệu để tính MACD Signal Line."}

    signal_line = np.convolve(macd_line, np.ones(signal_period)/signal_period, mode="valid")

    return [{"time": ema_short[i + signal_period - 1]["time"], "macd": float(macd_line[i + signal_period - 1]), "signal": float(signal_line[i])} for i in range(len(signal_line))]

# 🔥 6. Tính Bollinger Bands (Dải Bollinger)
def calculate_bollinger_bands(ohlcv, period=20, std_dev=2):
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính Bollinger Bands."}

    close_prices = np.array([candle["close"] for candle in ohlcv], dtype=float)
    sma = np.convolve(close_prices, np.ones(period)/period, mode="valid")
    std = np.array([np.std(close_prices[i - period + 1:i + 1]) for i in range(period - 1, len(close_prices))])

    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)

    return [{"time": ohlcv[i + period - 1]["time"], "sma": float(sma[i]), "upper_band": float(upper_band[i]), "lower_band": float(lower_band[i])} for i in range(len(sma))]

# 🔥 7. Tính ATR (Average True Range)
def calculate_atr(ohlcv, period=14):
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính ATR."}

    true_ranges = np.array([
        max(
            ohlcv[i]["high"] - ohlcv[i]["low"],
            abs(ohlcv[i]["high"] - ohlcv[i-1]["close"]),
            abs(ohlcv[i]["low"] - ohlcv[i-1]["close"])
        )
        for i in range(1, len(ohlcv))
    ], dtype=float)

    atr_values = np.convolve(true_ranges, np.ones(period)/period, mode="valid")

    return [{"time": ohlcv[i + period]["time"], "atr": float(atr_values[i])} for i in range(len(atr_values))]
 
 

# 🔥 1. Tính Volume Profile (Chia khối lượng giao dịch theo vùng giá)
def calculate_volume_profile(ohlcv, bins=24):
    if len(ohlcv) < bins:
        return {"error": "Không đủ dữ liệu để tính Volume Profile."}

    price_levels = np.linspace(min([c["low"] for c in ohlcv]), max([c["high"] for c in ohlcv]), bins)
    volume_at_levels = np.zeros(bins)

    for candle in ohlcv:
        index = np.argmin(np.abs(price_levels - candle["close"]))
        volume_at_levels[index] += candle["volume"]

    max_volume_price = price_levels[np.argmax(volume_at_levels)]
    return {"max_volume_price": max_volume_price}

# 🔥 2. Tính Mean Reversion (Kiểm tra nếu giá chạm Bollinger Bands)
def check_mean_reversion(ohlcv, bollinger_bands):
    if not isinstance(bollinger_bands, list) or len(bollinger_bands) < 1:
        return False  # Trả về False nếu dữ liệu không hợp lệ

    last_bollinger = bollinger_bands[-1]  # Lấy chỉ báo Bollinger Bands mới nhất

    if not isinstance(last_bollinger, dict):  # Kiểm tra lại kiểu dữ liệu
        return False

    last_close = ohlcv[-1]["close"]
    lower_band = last_bollinger.get("lower_band", None)
    upper_band = last_bollinger.get("upper_band", None)

    if lower_band is None or upper_band is None:
        return False  # Trả về False nếu dữ liệu thiếu

    return last_close <= lower_band or last_close >= upper_band

 

def calculate_adx(ohlcv, period=14):
    """Tính toán ADX (Average Directional Index) để đo sức mạnh xu hướng thị trường."""
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính ADX."}

    high_prices = np.array([candle["high"] for candle in ohlcv])
    low_prices = np.array([candle["low"] for candle in ohlcv])
    close_prices = np.array([candle["close"] for candle in ohlcv])

    # Tính +DM và -DM
    plus_dm = np.maximum(high_prices[1:] - high_prices[:-1], 0)
    minus_dm = np.maximum(low_prices[:-1] - low_prices[1:], 0)

    # Tránh lỗi chia cho 0
    sum_plus_dm = np.sum(plus_dm)
    sum_minus_dm = np.sum(minus_dm)

    plus_di = 100 * (plus_dm / sum_plus_dm) if sum_plus_dm > 0 else np.zeros_like(plus_dm)
    minus_di = 100 * (minus_dm / sum_minus_dm) if sum_minus_dm > 0 else np.zeros_like(minus_dm)

    # 🔥 Fix lỗi chia cho 0 khi `plus_di + minus_di == 0`
    denominator = np.where((plus_di + minus_di) == 0, 1, plus_di + minus_di)
    dx = np.abs(plus_di - minus_di) / denominator * 100
    dx = np.nan_to_num(dx, nan=0.0, posinf=0.0, neginf=0.0)  # Thay thế NaN/Inf bằng 0

    # Tính trung bình ADX
    adx = np.convolve(dx, np.ones(period) / period, mode="valid")

    return [{"time": ohlcv[i + period - 1]["time"], "adx": float(adx[i])} for i in range(len(adx))]



# 🔥 3. Kiểm tra điều kiện Grid Trading (ATR cao nhưng không có xu hướng mạnh)
def check_grid_trading(atr_data, rsi_data):
    return atr_data[-1]["atr"] > atr_data[-10]["atr"] * 1.5 and 40 < rsi_data[-1]["rsi"] < 60

# 🔥 4. Kiểm tra Market Making (Open Interest cao)
def check_market_making(open_interest):
    return open_interest["open_interest"] > 100000

# 🔥 1. Tính Ichimoku Cloud
def calculate_ichimoku(ohlcv, tenkan_period=9, kijun_period=26, senkou_period=52):
    if len(ohlcv) < senkou_period:
        return {"error": "Không đủ dữ liệu để tính Ichimoku Cloud."}

    highs = np.array([candle["high"] for candle in ohlcv])
    lows = np.array([candle["low"] for candle in ohlcv])

    tenkan_sen = (np.max(highs[-tenkan_period:]) + np.min(lows[-tenkan_period:])) / 2
    kijun_sen = (np.max(highs[-kijun_period:]) + np.min(lows[-kijun_period:])) / 2
    senkou_span_a = (tenkan_sen + kijun_sen) / 2
    senkou_span_b = (np.max(highs[-senkou_period:]) + np.min(lows[-senkou_period:])) / 2

    return {
        "tenkan_sen": tenkan_sen,
        "kijun_sen": kijun_sen,
        "senkou_span_a": senkou_span_a,
        "senkou_span_b": senkou_span_b
    }

# 🔥 2. Tính Golden Cross (EMA 50 & EMA 200)
def calculate_golden_cross(ohlcv, short_period=50, long_period=200):
    if len(ohlcv) < long_period:
        return {"ema_50": None, "ema_200": None, "golden_cross": False, "error": "Không đủ dữ liệu để tính Golden Cross."}

    close_prices = np.array([candle["close"] for candle in ohlcv])
    
    # Tính EMA bằng cách sử dụng công thức trung bình động lũy thừa
    ema_short = np.convolve(close_prices, np.ones(short_period)/short_period, mode="valid")
    ema_long = np.convolve(close_prices, np.ones(long_period)/long_period, mode="valid")

    return {
        "ema_50": float(ema_short[-1]) if len(ema_short) > 0 else None,
        "ema_200": float(ema_long[-1]) if len(ema_long) > 0 else None,
        "golden_cross": bool(len(ema_short) > 0 and len(ema_long) > 0 and ema_short[-1] > ema_long[-1])
    }


# 🔥 3. Tính VWAP
def calculate_vwap(ohlcv):
    total_volume = sum(candle["volume"] for candle in ohlcv)
    total_vwap = sum((candle["high"] + candle["low"] + candle["close"]) / 3 * candle["volume"] for candle in ohlcv)

    return {"vwap": total_vwap / total_volume if total_volume != 0 else 0}

# 🔥 4. Tính Pivot Points
def calculate_pivot_points(ohlcv):
    if len(ohlcv) < 2:
        return {"error": "Không đủ dữ liệu để tính Pivot Points."}

    last_candle = ohlcv[-2]
    pivot = (last_candle["high"] + last_candle["low"] + last_candle["close"]) / 3
    r1 = (2 * pivot) - last_candle["low"]
    s1 = (2 * pivot) - last_candle["high"]

    return {"pivot": pivot, "resistance_1": r1, "support_1": s1}

if __name__ == "__main__":
    symbol = config.TRADE_PAIR_SPOT_BTCUSDT

    # Lấy dữ liệu OHLCV
    ohlcv_data = get_ohlcv(symbol)

    # Tính chỉ số kỹ thuật
    sma_data = calculate_sma(ohlcv_data, period=14)
    ema_data = calculate_ema(ohlcv_data, period=14)
    rsi_data = calculate_rsi(ohlcv_data, period=14)
    macd_data = calculate_macd(ohlcv_data)
    bollinger_bands = calculate_bollinger_bands(ohlcv_data)
    atr = calculate_atr(ohlcv_data)

    print("\n✅ SMA 14:", sma_data[-5:])
    print("\n✅ EMA 14:", ema_data[-5:])
    print("\n✅ RSI 14:", rsi_data[-5:])
    print("\n✅ MACD:", macd_data[-5:])
    print("\n✅ Bollinger Bands:", bollinger_bands[-5:])
    print("\n✅ ATR:", atr[-5:])
