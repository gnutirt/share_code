import Binance_bot_trade.connection.connect_binance_future as connect_binance_future
import Binance_bot_trade.config.config as config
import numpy as np

client_futures = connect_binance_future.client_futures  # Kết nối Binance Futures

# 🔥 1. Lấy dữ liệu giá & volume (OHLCV) cho Futures
def get_futures_ohlcv(symbol=config.TRADE_PAIR_FUTURES_BTCUSDT, interval="1h", limit=100):
    """
    Lấy dữ liệu nến (OHLCV) trên Binance Futures.
    """
    try:
        klines = client_futures.futures_klines(symbol=symbol, interval=interval, limit=limit)
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

# 🔥 2. Lấy Funding Rate (Lãi suất hợp đồng Futures)
def get_funding_rate(symbol=config.TRADE_PAIR_FUTURES_BTCUSDT):
    """
    Lấy Funding Rate hiện tại trên Binance Futures.
    """
    try:
        funding = client_futures.futures_funding_rate(symbol=symbol, limit=1)
        return {
            "time": funding[0]["fundingTime"],
            "funding_rate": float(funding[0]["fundingRate"])
        }
    except Exception as e:
        return {"error": str(e)}

# 🔥 3. Lấy Open Interest (Tổng vị thế mở)

import numpy as np

# 📊 Phân tích dữ liệu Kline để lấy RSI, EMA, MACD
def analyze_kline(ohlcv, rsi_period=14, ema_period=50, short_macd=12, long_macd=26, signal_macd=9):
    if len(ohlcv) < max(rsi_period, ema_period, long_macd):
        return None, None, None  # Không đủ dữ liệu để tính toán

    close_prices = np.array([candle["close"] for candle in ohlcv])

    # ✅ 1. Tính RSI
    deltas = np.diff(close_prices)
    gain = np.maximum(deltas, 0)
    loss = np.abs(np.minimum(deltas, 0))

    avg_gain = np.convolve(gain, np.ones(rsi_period) / rsi_period, mode="valid")
    avg_loss = np.convolve(loss, np.ones(rsi_period) / rsi_period, mode="valid")

    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    rsi = float(rsi_values[-1]) if len(rsi_values) > 0 else None

    # ✅ 2. Tính EMA
    ema_values = np.zeros_like(close_prices, dtype=float)
    multiplier = 2 / (ema_period + 1)
    ema_values[ema_period - 1] = np.mean(close_prices[:ema_period])

    for i in range(ema_period, len(close_prices)):
        ema_values[i] = (close_prices[i] - ema_values[i - 1]) * multiplier + ema_values[i - 1]
    ema = float(ema_values[-1]) if len(ema_values) > 0 else None

    # ✅ 3. Tính MACD
    ema_short = np.zeros_like(close_prices, dtype=float)
    ema_long = np.zeros_like(close_prices, dtype=float)

    multiplier_short = 2 / (short_macd + 1)
    multiplier_long = 2 / (long_macd + 1)

    ema_short[short_macd - 1] = np.mean(close_prices[:short_macd])
    ema_long[long_macd - 1] = np.mean(close_prices[:long_macd])

    for i in range(short_macd, len(close_prices)):
        ema_short[i] = (close_prices[i] - ema_short[i - 1]) * multiplier_short + ema_short[i - 1]

    for i in range(long_macd, len(close_prices)):
        ema_long[i] = (close_prices[i] - ema_long[i - 1]) * multiplier_long + ema_long[i - 1]

    macd_line = ema_short - ema_long
    signal_line = np.convolve(macd_line, np.ones(signal_macd) / signal_macd, mode="valid")

    macd = float(macd_line[-1]) if len(macd_line) > 0 else None
    signal = float(signal_line[-1]) if len(signal_line) > 0 else None

    return rsi, ema, macd


def get_open_interest(symbol=config.TRADE_PAIR_FUTURES_BTCUSDT):
    """
    Lấy Open Interest hiện tại trên Binance Futures.
    """
    try:
        open_interest = client_futures.futures_open_interest(symbol=symbol)
        return {
            "symbol": symbol,
            "open_interest": float(open_interest["openInterest"])
        }
    except Exception as e:
        return {"error": str(e)}

# 🔥 4. Tính SMA (Trung bình động đơn giản)
def calculate_sma(ohlcv, period=14):
    if len(ohlcv) < period:
        return {"error": "Không đủ dữ liệu để tính SMA."}
    
    close_prices = np.array([candle["close"] for candle in ohlcv])
    sma_values = np.convolve(close_prices, np.ones(period)/period, mode="valid")

    return [{"time": ohlcv[i + period - 1]["time"], "sma": float(sma_values[i])} for i in range(len(sma_values))]

# 🔥 5. Tính RSI (Chỉ số sức mạnh tương đối)
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

 

def calculate_atr(ohlcv, period=14):
    """
    Tính Average True Range (ATR) từ dữ liệu OHLCV.
    :param ohlcv: Danh sách nến OHLCV, mỗi nến là một dict với các khóa 'open', 'high', 'low', 'close', 'volume'.
    :param period: Số chu kỳ để tính ATR (mặc định là 14).
    :return: Danh sách dict chứa 'time' và 'atr'.
    """
    if len(ohlcv) < period + 1:
        raise ValueError("Không đủ dữ liệu để tính ATR.")

    high_prices = np.array([candle['high'] for candle in ohlcv])
    low_prices = np.array([candle['low'] for candle in ohlcv])
    close_prices = np.array([candle['close'] for candle in ohlcv])

    # Tính True Range (TR)
    tr = np.maximum(high_prices[1:] - low_prices[1:], 
                    np.maximum(np.abs(high_prices[1:] - close_prices[:-1]), 
                               np.abs(low_prices[1:] - close_prices[:-1])))

    # Tính ATR bằng cách lấy trung bình động giản đơn (SMA) của TR
    atr = np.zeros_like(tr)
    atr[:period] = np.mean(tr[:period])
    for i in range(period, len(tr)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    # Chuẩn bị kết quả
    atr_values = [{'time': ohlcv[i + 1]['time'], 'atr': atr[i - period + 1]} for i in range(period - 1, len(tr))]

    return atr_values


def calculate_macd(ohlcv, short_period=12, long_period=26, signal_period=9):
    """
    Tính MACD từ dữ liệu OHLCV
    :param ohlcv: Danh sách nến OHLCV
    :param short_period: EMA ngắn hạn (Mặc định 12)
    :param long_period: EMA dài hạn (Mặc định 26)
    :param signal_period: EMA tín hiệu (Mặc định 9)
    :return: Danh sách MACD và đường tín hiệu
    """
    if len(ohlcv) < long_period:
        return {"error": "Không đủ dữ liệu để tính MACD."}

    close_prices = np.array([candle["close"] for candle in ohlcv])

    # Tính EMA ngắn hạn & EMA dài hạn
    ema_short = np.zeros_like(close_prices, dtype=float)
    ema_long = np.zeros_like(close_prices, dtype=float)

    multiplier_short = 2 / (short_period + 1)
    multiplier_long = 2 / (long_period + 1)

    ema_short[short_period - 1] = np.mean(close_prices[:short_period])
    ema_long[long_period - 1] = np.mean(close_prices[:long_period])

    for i in range(short_period, len(close_prices)):
        ema_short[i] = (close_prices[i] - ema_short[i - 1]) * multiplier_short + ema_short[i - 1]

    for i in range(long_period, len(close_prices)):
        ema_long[i] = (close_prices[i] - ema_long[i - 1]) * multiplier_long + ema_long[i - 1]

    # Tính MACD Line
    macd_line = ema_short - ema_long
    signal_line = np.convolve(macd_line, np.ones(signal_period) / signal_period, mode="valid")

    return [{"time": ohlcv[i]["time"], "macd": float(macd_line[i]), "signal": float(signal_line[i - (signal_period - 1)])}
            for i in range(signal_period - 1, len(macd_line))]
 

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


# 🔥 3. Kiểm tra điều kiện Grid Trading (ATR cao nhưng không có xu hướng mạnh)
def check_grid_trading(ohlcv, rsi_data, atr_data):
    """ Kiểm tra nếu ATR cao nhưng không có xu hướng mạnh (RSI trung lập) để sử dụng Grid Trading """
    if len(atr_data) < 10 or len(rsi_data) < 10:
        return False  # Tránh lỗi nếu dữ liệu không đủ

    atr_high = atr_data[-1]["atr"] > atr_data[-10]["atr"] * 1.5
    rsi_neutral = 40 < rsi_data[-1]["rsi"] < 60  # Không quá mua, không quá bán

    return atr_high and rsi_neutral


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
        return {
            "ema_50": None,
            "ema_200": None,
            "golden_cross": False,  # ✅ Trả về False thay vì không có key
            "error": "Không đủ dữ liệu để tính Golden Cross."
        }

    close_prices = np.array([candle["close"] for candle in ohlcv])
    
    ema_short = np.convolve(close_prices, np.ones(short_period)/short_period, mode="valid")
    ema_long = np.convolve(close_prices, np.ones(long_period)/long_period, mode="valid")

    return {
        "ema_50": float(ema_short[-1]) if len(ema_short) > 0 else None,
        "ema_200": float(ema_long[-1]) if len(ema_long) > 0 else None,
        "golden_cross": bool(len(ema_short) > 0 and len(ema_long) > 0 and ema_short[-1] > ema_long[-1])
    }
def get_open_interest(symbol):
    """ Lấy Open Interest hiện tại của Futures """
    try:
        response = client_futures.futures_open_interest(symbol=symbol)
        return {"symbol": symbol, "open_interest": float(response["openInterest"])}
    except Exception as e:
        print(f"❌ Lỗi khi lấy Open Interest: {e}")
        return {"symbol": symbol, "open_interest": None}
 

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
    symbol = config.TRADE_PAIR_FUTURES_BTCUSDT

    # Lấy dữ liệu Futures OHLCV
    ohlcv_data = get_futures_ohlcv(symbol)

    # Lấy Funding Rate
    funding_rate = get_funding_rate(symbol)

    # Lấy Open Interest
    open_interest = get_open_interest(symbol)

    # Tính chỉ số kỹ thuật
    sma_data = calculate_sma(ohlcv_data, period=14)
    rsi_data = calculate_rsi(ohlcv_data, period=14)
    bollinger_bands = calculate_bollinger_bands(ohlcv_data)

    print("\n✅ Funding Rate:", funding_rate)
    print("\n✅ Open Interest:", open_interest)
    print("\n✅ SMA 14:", sma_data[-5:])
    print("\n✅ RSI 14:", rsi_data[-5:])
    print("\n✅ Bollinger Bands:", bollinger_bands[-5:])
