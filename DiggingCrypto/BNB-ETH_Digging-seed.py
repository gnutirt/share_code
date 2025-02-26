import time
import secrets
from datetime import datetime
from mnemonic import Mnemonic  # Thư viện BIP-39
from eth_account import Account
from web3 import Web3
import logging

# Kích hoạt tính năng HD Wallet của eth_account
Account.enable_unaudited_hdwallet_features()

# Định nghĩa các URL RPC
BNB_RPC_URL = "https://bsc-dataseed.binance.org/"  # RPC của BNB Chain
ETH_RPC_URL = "https://rpc.ankr.com/eth"  # RPC của ETH Mainnet

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("wallet_log_mnemonic.log", mode='a', encoding="utf-8")
    ]
)

# Kết nối với RPC
def connect_rpc(rpc_url):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        logging.error(f"Không thể kết nối đến RPC: {rpc_url}")
        return None
    return web3

# Tạo seed words (mnemonic) ngẫu nhiên
def generate_seed_words():
    mnemo = Mnemonic("english")
    entropy = secrets.token_bytes(16)  # 128-bit entropy cho 12 từ
    seed_words = mnemo.to_mnemonic(entropy)
    return seed_words

# Tạo private key từ mnemonic
def generate_from_mnemonic(mnemonic, derivation_path="m/44'/60'/0'/0/0"):
    mnemo = Mnemonic("english")
    if not mnemo.check(mnemonic):
        return None  # Nếu mnemonic không hợp lệ
    account = Account.from_mnemonic(mnemonic, account_path=derivation_path)
    return account.key.hex()  # Sử dụng 'key' thay vì 'privateKey'

# Kiểm tra số dư
def check_balance(web3, address):
    try:
        balance = web3.eth.get_balance(address)
        return web3.from_wei(balance, "ether")
    except Exception as e:
        logging.warning(f"Lỗi khi kiểm tra số dư {address}: {str(e)}")
        return 0

# Ghi log ví có số dư
def log_wallet(chain, mnemonic, private_key, address, balance):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{chain.upper()}] Mnemonic: {mnemonic}, Private Key: {private_key}, Address: {address}, Balance: {balance}"
    logging.info(log_message)
    print(f"\n[LƯU]: {chain.upper()} Address: {address} với số dư {balance}")

# Chương trình chính
def main():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Chương trình bắt đầu vào lúc: {start_time}")

    # Tùy chọn chain
    # option = input("Chọn chain (bnb/eth/both): ").strip().lower()
    option ="both"
    # delay = float(input("Nhập thời gian nghỉ giữa các lần kiểm tra (giây): ").strip())
    delay = 0
    # max_attempts = int(input("Nhập số lượng mnemonic tối đa cần kiểm tra: "))
    max_attempts = 1000000000000

    # Kết nối RPC
    web3_bnb = connect_rpc(BNB_RPC_URL) if option in ("bnb", "both") else None
    web3_eth = connect_rpc(ETH_RPC_URL) if option in ("eth", "both") else None

    if not web3_bnb and not web3_eth:
        logging.error("Không thể kết nối đến bất kỳ chain nào.")
        return

    logging.info(f"Đã kết nối thành công đến {option.upper()} blockchain.")
    print("Bắt đầu kiểm tra mnemonic ngẫu nhiên... Nhấn Ctrl+C để dừng.")

    try:
        for idx in range(1, max_attempts + 1):
            mnemonic = generate_seed_words()  # Tạo mnemonic ngẫu nhiên
            private_key = generate_from_mnemonic(mnemonic)
            if not private_key:
                logging.warning(f"Mnemonic không hợp lệ: {mnemonic}")
                continue

            short_mnemonic = f"{mnemonic[:10]}..."
            short_private_key = f"{private_key[:6]}...{private_key[-4:]}"

            # Kiểm tra trên BNB Chain
            if web3_bnb:
                address_bnb = web3_bnb.eth.account.from_key(private_key).address
                balance_bnb = check_balance(web3_bnb, address_bnb)
                print(
                    f"\rMnemonic No: {idx}, {short_mnemonic}, [BNB] Address: {address_bnb[:6]}...{address_bnb[-4:]}, Balance: {balance_bnb} BNB",
                    end="",
                    flush=True,
                )
                if balance_bnb > 0:
                    print("bnb", mnemonic, private_key, address_bnb, balance_bnb)
                    log_wallet("bnb", mnemonic, private_key, address_bnb, balance_bnb)

            # Kiểm tra trên ETH Chain
            if web3_eth:
                address_eth = web3_eth.eth.account.from_key(private_key).address
                balance_eth = check_balance(web3_eth, address_eth)
                print(
                    f"\rMnemonic No: {idx}, {short_mnemonic}, [ETH] Address: {address_eth[:6]}...{address_eth[-4:]}, Balance: {balance_eth} ETH",
                    end="",
                    flush=True,
                )
                if balance_eth > 0:
                    print("eth", mnemonic, private_key, address_eth, balance_eth)
                    log_wallet("eth", mnemonic, private_key, address_eth, balance_eth)

            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nChương trình đã dừng.")
    finally:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Chương trình kết thúc vào lúc: {end_time}, Tổng số mnemonic đã kiểm tra: {idx}")

if __name__ == "__main__":
    main()