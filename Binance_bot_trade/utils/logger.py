import csv
import os
import logging
from datetime import datetime

# Cấu hình thư mục và file log
# Tạo thư mục logs nếu chưa có
os.makedirs("logs", exist_ok=True)

# Cấu hình logger để lưu log vào file
LOG_FILE = "./logs/bot_trading.log"
LOG_DIR = "logs"
 
TRADE_LOG_FILE = os.path.join(LOG_DIR, "trade_log.csv")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error_log.txt")

# Đảm bảo thư mục logs tồn tại
os.makedirs(LOG_DIR, exist_ok=True)

# Cấu hình logging
# logging.basicConfig(
#     filename=os.path.join(LOG_DIR, "bot_runtime.log"),
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s", 
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding="utf-8"),
        logging.StreamHandler()  # In log ra console
    ]
)
def log_trade(trade_type, symbol, price, quantity, strategy, status="SUCCESS"):
    """
    Ghi log giao dịch vào CSV.
    
    :param trade_type: Loại giao dịch (BUY/SELL)
    :param symbol: Cặp giao dịch (VD: BTCUSDT)
    :param price: Giá thực hiện giao dịch
    :param quantity: Khối lượng giao dịch
    :param strategy: Chiến lược giao dịch sử dụng
    :param status: Trạng thái giao dịch (SUCCESS/FAILED)
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = [timestamp, trade_type, symbol, price, quantity, strategy, status]

        file_exists = os.path.isfile(TRADE_LOG_FILE)

        with open(TRADE_LOG_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Trade Type", "Symbol", "Price", "Quantity", "Strategy", "Status"])
            writer.writerow(log_entry)

        logging.info(f"📊 Giao dịch đã được ghi log: {log_entry}")
    except Exception as e:
        log_error(f"Lỗi khi ghi log giao dịch: {e}")

def log_error(error_message):
    """
    Ghi log lỗi vào file error_log.txt.
    
    :param error_message: Thông báo lỗi cần ghi lại.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ERROR_LOG_FILE, "a") as file:
            file.write(f"{timestamp} - ERROR: {error_message}\n")

        logging.error(f"❌ Lỗi đã được ghi log: {error_message}")
    except Exception as e:
        print(f"⚠️ Không thể ghi log lỗi: {e}")

def save_strategy_history(trade_mode, selected_strategies, market_data):
    """
    Ghi log chiến lược đã sử dụng vào CSV.

    :param trade_mode: SPOT hoặc FUTURES.
    :param selected_strategies: Danh sách chiến lược đã áp dụng.
    :param market_data: Dữ liệu thị trường (giá đóng cửa, RSI, MACD, ATR).
    """
    try:
        strategy_log_file = os.path.join(LOG_DIR, "strategy_history.csv")
        fieldnames = ["timestamp", "trade_mode", "strategies", "close_price", "RSI", "MACD", "ATR"]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "timestamp": timestamp,
            "trade_mode": trade_mode,
            "strategies": ", ".join(selected_strategies) if selected_strategies else "NONE",
            "close_price": market_data.get("spot_price" if trade_mode == "SPOT" else "futures_price", None),
            "RSI": market_data.get("RSI", None),
            "MACD": market_data.get("MACD", None),
            "ATR": market_data.get("ATR", None),
        }

        file_exists = os.path.isfile(strategy_log_file)

        with open(strategy_log_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        logging.info(f"📊 Chiến lược đã được lưu vào {strategy_log_file}: {data}")
    except Exception as e:
        log_error(f"Lỗi khi ghi log chiến lược: {e}")
import os
import csv
from datetime import datetime
import logging

def log_trade_closure(symbol, position_type, entry_price, close_price, close_type, unrealized_profit, profit_percent):
    """ 
    Ghi log lệnh đóng vào CSV với đầy đủ thông tin 
    Nếu `position_size` không được truyền vào, mặc định là 1.0 để tránh lỗi.
    """

    file_path = "./logs/liquidation_log.csv"
    file_exists = os.path.isfile(file_path)  # Kiểm tra xem file đã tồn tại chưa
    position_size=1.0
    # Tính toán lợi nhuận hoặc lỗ (PnL)
    profit_loss = (close_price - entry_price) * position_size if position_type == "LONG" else (entry_price - close_price) * position_size

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Nếu file chưa tồn tại, ghi tiêu đề CSV
        if not file_exists:
            writer.writerow([
                "Timestamp", "Symbol", "Position Type", "Entry Price", "Close Price", 
                "Close Type", "PnL (USDT)", "Profit %", "Size"
            ])

        # Ghi dữ liệu lệnh đóng
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            position_type,
            round(entry_price, 4),
            round(close_price, 4),
            close_type,
            round(profit_loss, 4),
            round(profit_percent, 2),
            round(position_size, 6)
        ])
    
    logging.info(f"📜 Ghi log {close_type}: {symbol} {position_type} | Entry: {entry_price:.2f} → Close: {close_price:.2f} | "
                 f"PnL: {profit_loss:.2f} USDT | Profit: {profit_percent:.2f}% | Size: {position_size:.6f}")
