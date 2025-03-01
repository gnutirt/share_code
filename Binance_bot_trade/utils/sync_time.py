import time
import os
import logging
from binance.client import Client
import Binance_bot_trade.connection.connect_binance_future as connect_binance_future

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sync_time.log", mode="a", encoding="utf-8"),
    ]
)

def sync_time():
    client_futures = connect_binance_future.client_futures  # Kết nối Futures

    """ Đồng bộ thời gian local với Binance Server """
    try:
        server_time = client_futures.get_server_time()
        server_timestamp = server_time["serverTime"] / 1000  # Chuyển về giây
        local_timestamp = time.time()

        time_offset = server_timestamp - local_timestamp  # Tính độ lệch thời gian
        logging.info(f"⏳ Độ lệch thời gian: {time_offset:.3f} giây")

        if abs(time_offset) > 1:  # Chỉ cập nhật nếu chênh lệch lớn hơn 1 giây
            logging.warning("⚠️ Độ lệch thời gian quá lớn, thử đồng bộ lại hệ thống!")

            # Kiểm tra trạng thái dịch vụ Windows Time
            status = os.system("sc query w32time | findstr RUNNING")
            if status != 0:  # Dịch vụ chưa chạy
                logging.info("🔧 Khởi động dịch vụ Windows Time...")
                os.system("net start w32time")  # Khởi động dịch vụ (yêu cầu admin)

            # Cấu hình và đồng bộ thời gian
            os.system('w32tm /config /manualpeerlist:"time.nist.gov" /syncfromflags:manual /reliable:YES /update')
            os.system('w32tm /resync')  # Đồng bộ ngay lập tức

            # Kiểm tra lại độ lệch sau khi đồng bộ
            server_time = client_futures.get_server_time()
            server_timestamp = server_time["serverTime"] / 1000
            local_timestamp = time.time()
            new_offset = server_timestamp - local_timestamp
            logging.info(f"⏳ Độ lệch thời gian sau đồng bộ: {new_offset:.3f} giây")

    except Exception as e:
        logging.error(f"❌ Lỗi khi đồng bộ thời gian với Binance: {e}")

if __name__ == "__main__":
    # Kiểm tra quyền admin
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    if not is_admin:
        logging.error("❌ Vui lòng chạy chương trình với quyền quản trị (admin) để đồng bộ thời gian!")
        exit(1)

    while True:
        sync_time()
        print("✅ Đồng bộ thời gian với Binance thành công!")
        time.sleep(10)