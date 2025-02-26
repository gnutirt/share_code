import Binance_bot_trade.connection.connect_binance_future as connect_binance_future
import Binance_bot_trade.config.config as config

client_futures = connect_binance_future.client_futures  # Sử dụng client_futures từ file kết nối

# Hàm kiểm tra lịch sử giao dịch Futures và trả về danh sách giao dịch
def check_trade_history_futures(symbol, limit=100):
    print(f"\n📌 Kiểm tra lịch sử giao dịch Futures cho cặp {symbol}...")
    try:
        trades = client_futures.futures_account_trades(symbol=symbol, limit=limit)
        if not trades:
            print(f"❌ Không có giao dịch nào được tìm thấy cho cặp {symbol}.")
            return []
        
        trade_list = [
            {
                "id": trade["id"],
                "symbol": symbol,
                "price": trade["price"],
                "qty": trade["qty"],
                "side": "BUY" if trade["buyer"] else "SELL",
                "time": trade["time"]
            }
            for trade in trades
        ]

        return trade_list
    
    except Exception as e:
        print(f"❌ Lỗi khi lấy lịch sử giao dịch Futures ({symbol}): {e}")
        return []

if __name__ == "__main__":
    trade_pairs_futures = [
        config.TRADE_PAIR_FUTURES_BTCUSDT,
        config.TRADE_PAIR_FUTURES_ETHUSDT,
        config.TRADE_PAIR_FUTURES_BNBUSDT
    ]

    for pair in trade_pairs_futures:
        trade_history = check_trade_history_futures(pair)
        print(f"\n🔹 Lịch sử giao dịch Futures ({pair}):")
        for trade in trade_history:
            print(f"🔹 ID: {trade['id']} | Giá: {trade['price']} | Số lượng: {trade['qty']} | "
                  f"Loại: {trade['side']} | Thời gian: {trade['time']}")
