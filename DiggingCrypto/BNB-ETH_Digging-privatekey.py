import secrets
import time
from datetime import datetime
from web3 import Web3
import logging
 


# Định nghĩa các URL RPC
BNB_RPC_URL = "https://bsc-dataseed.binance.org/"  # RPC của BNB Chain
ETH_RPC_URL = "https://rpc.ankr.com/eth"  # RPC của ETH Mainnet


class IgnoreRPCErrorFilter(logging.Filter):
    def filter(self, record):
        # Chặn log có chứa thông điệp "An RPC error"
        return " An RPC error was returned by the node. Check the message provided in the error and any available logs for more information." not in record.getMessage()

for handler in logging.getLogger().handlers:
    handler.addFilter(IgnoreRPCErrorFilter())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Ghi log ra console
        logging.FileHandler("wallet_log_BNB-ETH_Digging.log", mode='a', encoding="utf-8")  # Ghi log vào file "wallet_log.log" ở chế độ append
    ]
)
# Kết nối với RPC
def connect_rpc(rpc_url):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        print(f"Không thể kết nối đến RPC: {rpc_url}")
        return None
    return web3

# Hàm sinh private key ngẫu nhiên
def generate_random_wallet():
    private_key = secrets.token_hex(32)  # Sinh private key ngẫu nhiên (256 bit)
    return private_key

# Hàm kiểm tra số dư
def check_balance(web3, address):
    try:
        balance = web3.eth.get_balance(address)  # Số dư basecoin (wei)
        return web3.from_wei(balance, "ether")  # Chuyển sang đơn vị Ether/BNB
    except Exception:
        return 0  # Trả về 0 nếu có lỗi

# Lưu vào log file



# Hàm log
def log_wallet(chain, private_key, address, balance):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{chain.upper()}] Private Key: {private_key}, Address: {address}, Balance: {balance}"
    
    # Ghi log vào file và console
    logging.info(log_message)
    
    # In ra console thông báo
    print(f"\n[LƯU]: {chain.upper()} Address: {address} với số dư {balance}")
# def log_wallet(chain, private_key, address, balance):
#     log_file_path = "wallet_log.txt"
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with open(log_file_path, "a") as log_file:
#         log_file.write(f"{timestamp} [{chain.upper()}] Private Key: {private_key}, Address: {address}, Balance: {balance}\n")
#     print(f"\n[LƯU]: {chain.upper()} Address: {address} với số dư {balance}")

# Chương trình chính
def main():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Chương trình bắt đầu vào lúc: {start_time}")
    # Lựa chọn chain
    # option = input("Chọn chain (bnb/eth/both): ").strip().lower()
    option = "both"
    # delay = float(input("Nhập thời gian nghỉ giữa các lần kiểm tra (giây): ").strip())
    delay = 0
    count = 0
    # Kết nối đến chain tương ứng
    web3_bnb = connect_rpc(BNB_RPC_URL) if option in ("bnb", "both") else None
    web3_eth = connect_rpc(ETH_RPC_URL) if option in ("eth", "both") else None

    if option not in ("bnb", "eth", "both") or (web3_bnb is None and web3_eth is None):
        print("Không thể kết nối đến bất kỳ chain nào.")
        exit()

    print(f"Đã kết nối thành công đến {option.upper()} blockchain.")
    print("Bắt đầu kiểm tra ví ngẫu nhiên... Nhấn Ctrl+C để dừng chương trình.")

    try:
        while True:
            count += 1
            private_key = generate_random_wallet()  # Sinh private key ngẫu nhiên
            short_private_key = f"{private_key[:6]}...{private_key[-4:]}"  # Cắt ngắn Private Key để in

            # Khởi tạo biến lưu số dư
            balance_bnb = None
            balance_eth = None
            address_bnb = None
            address_eth = None

            # Kiểm tra trên BNB Chain
            if web3_bnb:
                address_bnb = web3_bnb.eth.account.from_key(private_key).address
                balance_bnb = check_balance(web3_bnb, address_bnb)

            # Kiểm tra trên ETH Chain
            if web3_eth:
                address_eth = web3_eth.eth.account.from_key(private_key).address
                balance_eth = check_balance(web3_eth, address_eth)

            # In kết quả
            if option == "both":
                print(
                    f"\rWallet No: {count}, Privatekey: {private_key} [BNB] Address: {address_bnb[:6]}...{address_bnb[-4:]},{balance_bnb} BNB | "
                    f"{balance_eth} ETH",
                    end="",
                    flush=True,
                )
            elif option == "bnb" and balance_bnb is not None:
                print(
                    f"\r[BNB] Address: {address_bnb[:6]}...{address_bnb[-4:]}, Privatekey: {short_private_key}, Balance: {balance_bnb} BNB",
                    end="",
                    flush=True,
                )
            elif option == "eth" and balance_eth is not None:
                print(
                    f"\r[ETH] Address: {address_eth[:6]}...{address_eth[-4:]}, Privatekey: {short_private_key}, Balance: {balance_eth} ETH",
                    end="",
                    flush=True,
                )

            # Ghi log nếu có số dư
            if web3_bnb and balance_bnb > 0:           
                print(f"\n Found {balance_bnb} BNB at address: {address_bnb} with {private_key}")
                log_wallet("bnb", private_key, address_bnb, balance_bnb)
            if web3_eth and balance_eth > 0:
                print(f"\n Found {balance_eth} ETH at address: {address_eth} with {private_key}")
                log_wallet("eth", private_key, address_eth, balance_eth)

            time.sleep(delay)  # Nghỉ theo thời gian người dùng chỉ định
    except KeyboardInterrupt:
        print("\nChương trình đã dừng.")

# ### Test Area ###

# web3_bnb = connect_rpc(BNB_RPC_URL) 
# balance_bnb = check_balance(web3_bnb, "0x5c0D693B30D5e494421D0589729A26AB86ed1948")
# print(f"Số dư trên BNB: {balance_bnb} BNB")


if __name__ == "__main__":
    main()
