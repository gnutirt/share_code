import time
from binance.client import Client
import Binance_bot_trade.connection.connect_binance_future as connect_binance_future
import logging
import os
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
            logging.warning("⚠️ Độ lệch thời gian quá lớn, cập nhật lại hệ thống!")   

            # Cấu hình Windows để sử dụng time.nist.gov
            os.system('w32tm /config /manualpeerlist:"time.nist.gov" /syncfromflags:manual /reliable:YES /update')

            # # Đồng bộ thời gian ngay lập tức
            # os.system('w32tm /resync')


    except Exception as e:
        logging.error(f"❌ Lỗi khi đồng bộ thời gian với Binance: {e}")
 
if __name__ == "__main__":
    while True:
        sync_time()
        print("✅ Đồng bộ thời gian với Binance thành công!")
        time.sleep(10)