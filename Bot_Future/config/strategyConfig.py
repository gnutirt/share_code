# 🔥 CẤU HÌNH CÁC CHIẾN LƯỢC GIAO DỊCH

STRATEGIES = {
    # 📌 1. Ichimoku Cloud (Trend-following)
    "ICHIMOKU": {
        "TENKAN_PERIOD": 9,
        "KIJUN_PERIOD": 26,
        "SENKOU_PERIOD": 52,
        "applyField": ["SPOT", "FUTURES"]
    },

    # 📌 2. Golden Cross / Death Cross (Trend-following)
    "GOLDEN_CROSS": {
        "SHORT_EMA": 50,
        "LONG_EMA": 200,
        "applyField": ["SPOT"]
    },

    # 📌 3. Pivot Points (Breakout Strategy)
    "PIVOT_POINTS": {
        "LOOKBACK_PERIOD": 14,
        "applyField": ["FUTURES"]
    },

    # 📌 4. Volume Profile (Market Structure)
    "VOLUME_PROFILE": {
        "HISTOGRAM_BINS": 24,
        "applyField": ["FUTURES"]
    },

    # 📌 5. VWAP (Volume Weighted Average Price)
    "VWAP": {
        "PERIOD": "1D",
        "applyField": ["FUTURES"]
    },

    # 📌 6. Mean Reversion (Reversal Trading)
    "MEAN_REVERSION": {
        "SMA_PERIOD": 50,
        "applyField": ["SPOT"]
    },

    # 📌 7. Grid Trading (Automated Trading)
    "GRID_TRADING": {
        "GRID_SPACING": 0.5,
        "GRID_LEVELS": 10,
        "applyField": ["SPOT", "FUTURES"]
    },

    # 📌 8. Market Making (High-Frequency Trading - HFT)
    "MARKET_MAKING": {
        "SPREAD": 0.1,
        "ORDER_SIZE": 0.01,
        "applyField": ["FUTURES"]
    },

    # 📌 9. RSI + MACD (Trend-following)
    "RSI_MACD": {
        "RSI_PERIOD": 14,
        "RSI_OVERBOUGHT": 70,
        "RSI_OVERSOLD": 30,
        "MACD_SHORT_PERIOD": 12,
        "MACD_LONG_PERIOD": 26,
        "MACD_SIGNAL_PERIOD": 9,
        "applyField": ["SPOT", "FUTURES"]
    },

    # 📌 10. Bollinger Bands (Mean Reversion)
    "BOLLINGER_BANDS": {
        "BOLLINGER_PERIOD": 20,
        "BOLLINGER_STD_DEV": 2,
        "applyField": ["SPOT"]
    },

    # 📌 11. Breakout Strategy (Momentum Trading)
    "BREAKOUT": {
        "BREAKOUT_CONFIRMATION_VOLUME": 2,  # Volume tăng ít nhất 2 lần để xác nhận breakout
        "applyField": ["FUTURES"]
    },

    # 📌 12. Scalping EMA (High-Frequency Trading)
    "SCALPING": {
        "EMA_FAST": 5,
        "EMA_SLOW": 20,
        "TRADE_VOLUME_THRESHOLD": 1000,  # Chỉ vào lệnh nếu khối lượng cao
        "applyField": ["FUTURES"]
    }
}

def get_strategy_config(strategy_name):
    """
    Lấy cấu hình cho một chiến lược cụ thể.
    :param strategy_name: Tên chiến lược (VD: "RSI_MACD")
    :return: Dictionary chứa cấu hình chiến lược
    """
    return STRATEGIES.get(strategy_name, {})

def get_strategies_by_field(field):
    """
    Lấy danh sách các chiến lược phù hợp với Spot hoặc Futures.
    :param field: "SPOT" hoặc "FUTURES"
    :return: Danh sách chiến lược phù hợp
    """
    return {key: value for key, value in STRATEGIES.items() if field in value["applyField"]}

if __name__ == "__main__":
    # Ví dụ: Lấy thông tin của chiến lược RSI_MACD
    active_strategy = "RSI_MACD"
    print(f"\n✅ Cấu hình chiến lược {active_strategy}:")
    print(get_strategy_config(active_strategy))

    # Ví dụ: Lấy danh sách các chiến lược dành cho Futures
    print("\n✅ Danh sách chiến lược dành cho Futures:")
    print(get_strategies_by_field("FUTURES"))

    # Ví dụ: Lấy danh sách các chiến lược dành cho Spot
    print("\n✅ Danh sách chiến lược dành cho Spot:")
    print(get_strategies_by_field("SPOT"))
