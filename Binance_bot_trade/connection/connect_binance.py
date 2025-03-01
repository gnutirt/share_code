import connect_binance_spot
import connect_binance_future

def test_binance_connections():
    print("\n🔹🔹🔹 TEST KẾT NỐI BINANCE 🔹🔹🔹")

    print("\n--- 🔥 TEST SPOT BINANCE ---")
    connect_binance_spot.check_spot_balance()
    connect_binance_spot.get_spot_price()

    print("\n--- 🔥 TEST FUTURES BINANCE ---")
    connect_binance_future.check_futures_balance()
    connect_binance_future.get_futures_price()

if __name__ == "__main__":
    test_binance_connections()
