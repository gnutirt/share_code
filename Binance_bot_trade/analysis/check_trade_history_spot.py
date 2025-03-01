import Binance_bot_trade.connection.connect_binance_spot as connect_binance_spot
import Binance_bot_trade.config.config as config

client_spot = connect_binance_spot.client_spot  # Sử dụng client_spot từ file kết nối

# Hàm kiểm tra lịch sử giao dịch Spot và trả về danh sách giao dịch
def check_trade_history_spot(symbol, limit=100):
    print(f"\n📌 Kiểm tra lịch sử giao dịch Spot cho cặp {symbol}...")
    try:
        trades = client_spot.get_my_trades(symbol=symbol, limit=limit)
        if not trades:
            print(f"❌ Không có giao dịch nào được tìm thấy cho cặp {symbol}.")
            return []
        
        trade_list = [
            {
                "id": trade["id"],
                "symbol": symbol,
                "price": trade["price"],
                "qty": trade["qty"],
                "side": "BUY" if trade["isBuyer"] else "SELL",
                "time": trade["time"]
            }
            for trade in trades
        ]

        return trade_list
    
    except Exception as e:
        print(f"❌ Lỗi khi lấy lịch sử giao dịch Spot ({symbol}): {e}")
        return []

if __name__ == "__main__":
    trade_pairs_spot = [
        config.TRADE_PAIR_SPOT_BTCUSDT,
        config.TRADE_PAIR_SPOT_ETHUSDT,
        config.TRADE_PAIR_SPOT_BNBUSDT
    ]

    for pair in trade_pairs_spot:
        trade_history = check_trade_history_spot(pair)
        print(f"\n🔹 Lịch sử giao dịch Spot ({pair}):")
        for trade in trade_history:
            print(f"🔹 ID: {trade['id']} | Giá: {trade['price']} | Số lượng: {trade['qty']} | "
                  f"Loại: {trade['side']} | Thời gian: {trade['time']}")
