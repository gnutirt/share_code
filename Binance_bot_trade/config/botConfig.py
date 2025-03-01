# 🔥 CẤU HÌNH CHUNG CHO BOT
BOT_NAME = "CryptoTradingBot"
TRADE_MODE = "BOTH"  # "SPOT" hoặc "FUTURES" hoăc "BOTH"
TEST_MODE = False  # True: Chạy test, False: Chạy thật

# 🔥 CẶP GIAO DỊCH VÀ SỐ TIỀN GIAO DỊCH
TRADE_PAIRS = {
    "SPOT": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    "FUTURES": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
}
TRADE_AMOUNT = 0.01  # Số lượng coin giao dịch 


# 🔥 QUẢN LÝ VỐN
START_BALANCE = 1000  # Vốn khởi điểm (USDT)
RISK_PER_TRADE = 2  # % rủi ro trên mỗi giao dịch (2% của số dư)

MAX_CONCURRENT_POSITIONS = 20  # Số lượng vốn tối đa cùng lúc
MIN_TRADE_AMOUNT = 10  # Giá trị tối thiểu của mỗi lệnh (USDT)
POSITION_SIZE_PERCENT = 10  # Mỗi lệnh chiếm bao nhiêu % vốn (tự động tính toán)


# 🔥 QUẢN LÝ LỆNH
ORDER_TYPE = "MARKET"  # "MARKET" hoặc "LIMIT"
LIMIT_ORDER_PRICE_OFFSET = 10  # Khoảng giá so với thị trường khi đặt Limit Order
STOP_LOSS_PERCENT = 3  # SL ở mức lỗ tối đa 3%
STOP_LOSS_PERCENT_GRID_FUTURES = 50  # SL ở mức lớn nhat 100%
TAKE_PROFIT_PERCENT = 5  # TP ở mức lợi nhuận 5%
DAILY_MAX_LOSS = 10  # Nếu bot lỗ 10% tổng vốn trong ngày, dừng giao dịch
MAX_CONSECUTIVE_LOSSES = 3  # Nếu bot thua liên tục 3 lệnh, tạm dừng 1 giờ
DYNAMIC_POSITION_SIZING = True  # True: Bật tính năng này

TRADE_LEVERAGE = 25

# 🔥 CẤU HÌNH CHO FUTURES
FUNDING_RATE_THRESHOLD = 0.01  # Nếu Funding Rate cao hơn mức này, tránh vào lệnh
OPEN_INTEREST_THRESHOLD = 100000  # Nếu Open Interest lớn hơn mức này, tránh vào lệnh

# 🔥 CẤU HÌNH CẢNH BÁO
ENABLE_ALERTS = True
ALERT_RSI_THRESHOLD = 25  # Cảnh báo nếu RSI < 25
ALERT_PRICE_CHANGE_PERCENT = 5  # Cảnh báo nếu giá thay đổi > 5% trong 1 giờ
SEND_ALERT_TO_TELEGRAM = False  # True: Gửi cảnh báo Telegram, False: Không gửi

# 🔥 TỐI ƯU HIỆU SUẤT BOT
API_REQUEST_INTERVAL = 60  # Giây giữa mỗi request API
CHECK_PROFIT_INTERVAL = 5
CHECK_ORDER_INTERVAL = 60
MAX_API_CALLS_PER_MINUTE = 60  # Giới hạn số lần gọi API trong 1 phút

# 🔥 CHIẾN LƯỢC GIAO DỊCH
ACTIVE_STRATEGY = "RSI_MACD"  # Chiến lược mặc định (có thể thay đổi)

LOG_PERFORMANCE = True  # Bật tính năng ghi log hiệu suất
PERFORMANCE_REPORT_INTERVAL = "1D"  # Tổng hợp hiệu suất hàng ngày

# 🔥 CẤU HÌNH CHO GRID TRADING
GRID_ORDER_VALUE = 6 # Giá trị cơ bản cho lệnh grid - USD
MAX_CONCURRENT_TRADES = 20  # Số lượng lệnh tối đa cùng lúc
GRID_LEVELS = 20  # Số lượng mức giá trong lưới (5 lệnh LONG + 5 lệnh SHORT)
MAX_GRID_LEVELS = 20
MIN_GRID_LEVELS = 10
GRID_SPACING_PERCENT = 1.5  # Khoảng cách giữa các mức giá (1.5% mỗi mức)
GRID_TRADE_AMOUNT = 0.01  # Số lượng coin giao dịch cho mỗi mức
ADAPTIVE_GRID_SCALING = 1.5  # Scale luoi giá theo thị trường
ATR_MULTIPLIER = 1.5  # Nhân với ATR để tính toán vị thế
MAX_ORDER_WAIT_TIME = 3600  # lệnh nào 3 giờ thì xoá
MIN_ATR = 50  # USD
FORCE_TAKE_PROFIT = 3   #USD
ATR_SMOOTHING_WINDOW = 10
TP_PERCENT = 50
SL_PERCENT = 50
TRAILING_SL_PERCENT_1 = 5  # Khi giá tăng 5%, kích hoạt trailing stop
TRAILING_SL_PERCENT_2 = 10  # Khi giá tăng 10%, tiếp tục điều chỉnh trailing stop
TRAILING_SL_ADJUST_1 = 3  # Dời SL lên mức +3% từ Entry Price nếu giá tăng 10%
ACCEPTABLE_LOSS = 0 # USD Khoản lỗ chấp nhận được, bot sẽ gồng để lỗ khoảng bao nhiêu đô thì stop lệnh liền 

#Note: Bot đang test ở chế độ grid và mở 2 vị thế cùng 1 lúc - Long và Short
# Bot tự điều chỉnh lưới, tự lấy profit mong muốn, tự đặt lại lệnh, tự đặt Take Profit / Stop loss. 
# Vẫn còn đang ở demo - hehehe