import time
from Binance_bot_trade.actionBot import strategyChoose
import Binance_bot_trade.connection.connect_binance_future as connect_binance_future
import Binance_bot_trade.config.config as config 
import Binance_bot_trade.config.botConfig as botConfig
import Binance_bot_trade.analysis.update_price as update_price 
import logging 
client_futures = connect_binance_future.client_futures  # Kết nối Futures
# 🔥 Kiểm tra và cập nhật đòn bẩy (Leverage)
def check_and_update_leverage(symbol, desired_leverage):
    """
    Kiểm tra và cập nhật leverage nếu không khớp với cấu hình.

    :param symbol: Cặp giao dịch (VD: BTCUSDT)
    :param desired_leverage: Đòn bẩy mong muốn từ botConfig
    """
    try:
        # 🔥 Lấy mức đòn bẩy hiện tại
        account_info = client_futures.futures_account()
        current_leverage = None

        for pos in account_info["positions"]:
            if pos["symbol"] == symbol:
                current_leverage = int(pos["leverage"])
                break

        if current_leverage is None:
            print(f"❌ Không tìm thấy thông tin đòn bẩy hiện tại cho {symbol}!")
            return

        # 🔥 Lấy mức đòn bẩy tối đa có thể sử dụng
        bracket_info = client_futures.futures_leverage_bracket(symbol=symbol)

        if not bracket_info:
            print(f"❌ Không lấy được thông tin đòn bẩy cho {symbol}!")
            return

        max_leverage = max([bracket["initialLeverage"] for bracket in bracket_info[0]["brackets"]])

        # 🔥 Đảm bảo không vượt quá đòn bẩy tối đa
        if desired_leverage > max_leverage:
            print(f"⚠️ Đòn bẩy mong muốn ({desired_leverage}x) vượt quá giới hạn! Dùng {max_leverage}x.")
            desired_leverage = max_leverage

        # 🔥 Kiểm tra và cập nhật nếu cần
        if current_leverage != desired_leverage:
            print(f"⚠️ Đòn bẩy hiện tại của {symbol}: {current_leverage}x, cập nhật về {desired_leverage}x...")
            response = client_futures.futures_change_leverage(symbol=symbol, leverage=desired_leverage)

            if response.get("leverage") == desired_leverage:
                print(f"✅ Đòn bẩy đã cập nhật thành {desired_leverage}x!")
            else:
                print(f"❌ Cập nhật đòn bẩy thất bại: {response}")

        else:
            print(f"✅ Đòn bẩy {symbol} đã đúng ({current_leverage}x).")

    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra/cập nhật đòn bẩy: {e}")

# 🔥 1. Kiểm tra số dư USDT trước khi vào lệnh Futures
def get_futures_balance(asset="USDT"):
    print(f"\n📌 Kiểm tra số dư {asset} trên Futures...")
    try:
        account_info = client_futures.futures_account_balance(timestamp=int(time.time() * 1000))
        for balance in account_info:
            if balance["asset"] == asset:
                usdt_balance = float(balance["balance"])
                print(f"💰 Số dư {asset} Futures: {usdt_balance}")
                return usdt_balance
        print(f"❌ Không tìm thấy {asset} trong tài khoản Futures.")
        return 0.0
    except Exception as e:
        print(f"❌ Lỗi khi lấy số dư Futures: {e}")
        return 0.0

# 🔥 2. Đặt lệnh Market Long (Mở vị thế mua với giá thị trường)
def place_market_long(symbol, quantity, leverage=5):
    print(f"\n📌 Đặt lệnh Market Long Futures cho {symbol} - Số lượng: {quantity} | Đòn bẩy: {leverage}x")

    usdt_balance = get_futures_balance("USDT")  # Kiểm tra số dư USDT
    futures_price_info = update_price.get_futures_price(symbol)  # Lấy giá Futures từ update_price.py
    futures_price = futures_price_info["futures_price"]
    
    if futures_price is None:
        print(f"❌ Lỗi khi lấy giá {symbol}, không thể đặt lệnh!")
        return None

    required_margin = (quantity * futures_price) / leverage  # Số USDT cần ký quỹ

    if usdt_balance < required_margin:
        print(f"❌ Không đủ USDT! Cần {required_margin:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    try:
        order = client_futures.futures_create_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quantity=quantity
        )
        print(f"✅ Lệnh Market Long thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi đặt lệnh Market Long: {e}")
        return None


# 🔥 3. Đặt lệnh Market Short (Mở vị thế bán với giá thị trường)
def place_market_short(symbol, quantity, leverage=5):
    print(f"\n📌 Đặt lệnh Market Short Futures cho {symbol} - Số lượng: {quantity} | Đòn bẩy: {leverage}x")

    usdt_balance = get_futures_balance("USDT")  # Kiểm tra số dư USDT
    futures_price_info = update_price.get_futures_price(symbol)  # Lấy giá Futures từ update_price.py
    futures_price = futures_price_info["futures_price"]
    
    if futures_price is None:
        print(f"❌ Lỗi khi lấy giá {symbol}, không thể đặt lệnh!")
        return None

    required_margin = (quantity * futures_price) / leverage  # Số USDT cần ký quỹ

    if usdt_balance < required_margin:
        print(f"❌ Không đủ USDT! Cần {required_margin:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    try:
        order = client_futures.futures_create_order(
            symbol=symbol,
            side="SELL",
            type="MARKET",
            quantity=quantity
        )
        print(f"✅ Lệnh Market Short thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        print(f"❌ Lỗi khi đặt lệnh Market Short: {e}")
        return None

# 🔥 3. Đặt lệnh Limit Long (Mua ở mức giá cố định)
import Binance_bot_trade.connection.connect_binance_future as connect_binance_future
import Binance_bot_trade.config.config as config
import Binance_bot_trade.analysis.update_price as update_price

client_futures = connect_binance_future.client_futures  # Kết nối Futures

# 🔥 1. Đặt lệnh Limit Long (Mua ở mức giá cố định)
def place_limit_long(symbol, price, quantity):
    """
    Đặt lệnh Long Limit trên Futures với đòn bẩy từ botConfig.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param price: Giá đặt lệnh
    :param quantity: Số lượng đặt mua
    :return: Thông tin lệnh nếu thành công, None nếu thất bại
    """
    leverage = botConfig.TRADE_LEVERAGE  # Lấy đòn bẩy từ botConfig
    check_and_update_leverage(symbol, leverage)

    # 🔹 Lấy số dư USDT
    usdt_balance = get_futures_balance("USDT")

    # 🔹 Lấy giá Futures
    futures_price_info = update_price.get_futures_price(symbol)
    futures_price = futures_price_info.get("futures_price")

    if futures_price is None:
        logging.error(f"❌ Không thể lấy giá Futures cho {symbol}, không thể đặt lệnh!")
        return None

    # 🔹 Lấy thông tin tickSize & stepSize từ Binance
    exchange_info = client_futures.futures_exchange_info()
    tick_size = None
    step_size = None

    for symbol_info in exchange_info["symbols"]:
        if symbol_info["symbol"] == symbol:
            tick_size = float(symbol_info["filters"][0]["tickSize"])  # Độ chính xác giá
            step_size = float(symbol_info["filters"][2]["stepSize"])  # Độ chính xác số lượng
            break

    if tick_size is None or step_size is None:
        logging.error(f"❌ Không lấy được thông tin tickSize hoặc stepSize cho {symbol}")
        return None

    # 🔹 Làm tròn giá đặt lệnh theo tickSize
    price = round(price / tick_size) * tick_size

    # 🔹 Làm tròn số lượng theo stepSize
    quantity = round(quantity / step_size) * step_size

    # 🔹 Kiểm tra số USDT cần ký quỹ
    required_margin = (quantity * futures_price) / leverage  # Số USDT cần ký quỹ

    if usdt_balance < required_margin:
        logging.warning(f"❌ Không đủ USDT! Cần {required_margin:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    logging.info(f"\n📌 Đặt lệnh Limit Long Futures cho {symbol} - Giá: {price}, Số lượng: {quantity}, Đòn bẩy: {leverage}x")

    try:
        order = client_futures.futures_create_order(
            symbol=symbol,
            side="BUY",
            type="LIMIT",
            price=f"{price:.8f}",
            quantity=f"{quantity:.8f}",
            timeInForce="GTC"
        )
        logging.info(f"✅ Lệnh Limit Long thành công! Order ID: {order['orderId']}")
        return order
    except Exception as e:
        logging.error(f"❌ Lỗi khi đặt lệnh Limit Long: {e}")
        return None

def place_limit_long_with_stop_loss(symbol, price, quantity):
    """
    Đặt lệnh Long Limit trên Futures với đòn bẩy từ botConfig.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param price: Giá đặt lệnh
    :param quantity: Số lượng đặt mua
    :return: Thông tin lệnh nếu thành công, None nếu thất bại
    """
    leverage = botConfig.TRADE_LEVERAGE  # Lấy đòn bẩy từ botConfig
    stop_loss_percent = botConfig.STOP_LOSS_PERCENT_GRID_FUTURES
    check_and_update_leverage(symbol, leverage)

    # 🔹 Lấy số dư USDT
    usdt_balance = get_futures_balance("USDT")

    # 🔹 Lấy giá Futures
    futures_price_info = update_price.get_futures_price(symbol)
    futures_price = futures_price_info.get("futures_price")

    if futures_price is None:
        logging.error(f"❌ Không thể lấy giá Futures cho {symbol}, không thể đặt lệnh!")
        return None

    # 🔹 Lấy thông tin tickSize & stepSize từ Binance
    exchange_info = client_futures.futures_exchange_info()
    tick_size = None
    step_size = None

    for symbol_info in exchange_info["symbols"]:
        if symbol_info["symbol"] == symbol:
            tick_size = float(symbol_info["filters"][0]["tickSize"])  # Độ chính xác giá
            step_size = float(symbol_info["filters"][2]["stepSize"])  # Độ chính xác số lượng
            break

    if tick_size is None or step_size is None:
        logging.error(f"❌ Không lấy được thông tin tickSize hoặc stepSize cho {symbol}")
        return None

    # 🔹 Làm tròn giá đặt lệnh theo tickSize
    price = round(price / tick_size) * tick_size

    # 🔹 Làm tròn số lượng theo stepSize
    quantity = round(quantity / step_size) * step_size

    # 🔹 Kiểm tra số USDT cần ký quỹ
    required_margin = (quantity * futures_price) / leverage  # Số USDT cần ký quỹ
    # **🔥 Tính giá Stop-Loss chính xác**     
    stop_loss_price = price - (price * (stop_loss_percent / 100) / leverage)
    stop_loss_price = round(stop_loss_price / tick_size) * tick_size  # Làm tròn theo tickSize

    if usdt_balance < required_margin:
        logging.warning(f"❌ Không đủ USDT! Cần {required_margin:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    logging.info(f"\n📌 Đặt lệnh Limit Long Futures cho {symbol} - Giá: {price}, Số lượng: {quantity}, Đòn bẩy: {leverage}x")

    try:
        order = client_futures.futures_create_order(
            symbol=symbol,
            side="BUY",
            type="LIMIT",
            price=f"{price:.8f}",
            quantity=f"{quantity:.8f}",
            timeInForce="GTC",
            positionSide="LONG"
        )
        logging.info(f"✅ Lệnh Limit Long thành công! Order ID: {order['orderId']}")
       
        # # Đặt lệnh Stop Market để tự động cắt lỗ
        # logging.info(f"⚠️ Đặt Stop-Loss tại {stop_loss_price:.2f} USDT")
        # stop_order = client_futures.futures_create_order(
        #     symbol=symbol,
        #     side="SELL",
        #     type="STOP_MARKET",
        #     stopPrice=f"{stop_loss_price:.8f}",
        #     quantity=f"{quantity:.8f}",
        #     timeInForce="GTC"
        # )

        # logging.info(f"✅ Stop-Loss thành công! SL Price: {stop_loss_price:.2f} USDT")
        return order
    except Exception as e:
        logging.error(f"❌ Lỗi khi đặt lệnh Limit Long: {e}")
        return None


# 🔥 4. Đặt lệnh Limit Short (Bán ở mức giá cố định)
def place_limit_short(symbol, price, quantity):
    """
    Đặt lệnh Short Limit trên Futures với kiểm tra & cập nhật leverage trước khi đặt lệnh.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param price: Giá đặt lệnh
    :param quantity: Số lượng đặt bán
    :return: Thông tin lệnh nếu thành công, None nếu thất bại
    """
    leverage = botConfig.TRADE_LEVERAGE  # Lấy đòn bẩy từ botConfig
    stop_loss_percent = botConfig.STOP_LOSS_PERCENT_GRID_FUTURES
    check_and_update_leverage(symbol, leverage)  # Kiểm tra & cập nhật leverage

    # 🔹 Lấy số dư USDT
    usdt_balance = get_futures_balance("USDT")

    # 🔹 Lấy giá Futures
    futures_price_info = update_price.get_futures_price(symbol)
    futures_price = futures_price_info.get("futures_price")

    if futures_price is None:
        logging.error(f"❌ Không thể lấy giá Futures cho {symbol}, không thể đặt lệnh!")
        return None

    # 🔹 Lấy thông tin tickSize & stepSize từ Binance
    exchange_info = client_futures.futures_exchange_info()
    tick_size = None
    step_size = None

    for symbol_info in exchange_info["symbols"]:
        if symbol_info["symbol"] == symbol:
            tick_size = float(symbol_info["filters"][0]["tickSize"])  # Độ chính xác giá
            step_size = float(symbol_info["filters"][2]["stepSize"])  # Độ chính xác số lượng
            break

    if tick_size is None or step_size is None:
        logging.error(f"❌ Không lấy được thông tin tickSize hoặc stepSize cho {symbol}")
        return None

    # 🔹 Làm tròn giá đặt lệnh theo tickSize
    price = round(price / tick_size) * tick_size

    # 🔹 Làm tròn số lượng theo stepSize
    quantity = round(quantity / step_size) * step_size

    # 🔹 Kiểm tra số USDT cần ký quỹ
    required_margin = (quantity * futures_price) / leverage  # Số USDT cần ký quỹ

    if usdt_balance < required_margin:
        logging.warning(f"❌ Không đủ USDT! Cần {required_margin:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    logging.info(f"\n📌 Đặt lệnh Limit Short Futures cho {symbol} - Giá: {price}, Số lượng: {quantity}, Đòn bẩy: {leverage}x")

    try:
        order = client_futures.futures_create_order(
            symbol=symbol,
            side="SELL",
            type="LIMIT",
            price=f"{price:.8f}",
            quantity=f"{quantity:.8f}",
            timeInForce="GTC"
        )
        logging.info(f"✅ Lệnh Limit Short thành công! Order ID: {order['orderId']}")
      
        return order
    except Exception as e:
        logging.error(f"❌ Lỗi khi đặt lệnh Limit Short: {e}")
        return None
def place_limit_short_with_stop_loss(symbol, price, quantity):
    """
    Đặt lệnh Short Limit trên Futures với kiểm tra & cập nhật leverage trước khi đặt lệnh.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param price: Giá đặt lệnh
    :param quantity: Số lượng đặt bán
    :return: Thông tin lệnh nếu thành công, None nếu thất bại
    """
    leverage = botConfig.TRADE_LEVERAGE  # Lấy đòn bẩy từ botConfig
    stop_loss_percent = botConfig.STOP_LOSS_PERCENT_GRID_FUTURES
    check_and_update_leverage(symbol, leverage)  # Kiểm tra & cập nhật leverage

    # 🔹 Lấy số dư USDT
    usdt_balance = get_futures_balance("USDT")

    # 🔹 Lấy giá Futures
    futures_price_info = update_price.get_futures_price(symbol)
    futures_price = futures_price_info.get("futures_price")

    if futures_price is None:
        logging.error(f"❌ Không thể lấy giá Futures cho {symbol}, không thể đặt lệnh!")
        return None

    # 🔹 Lấy thông tin tickSize & stepSize từ Binance
    exchange_info = client_futures.futures_exchange_info()
    tick_size = None
    step_size = None

    for symbol_info in exchange_info["symbols"]:
        if symbol_info["symbol"] == symbol:
            tick_size = float(symbol_info["filters"][0]["tickSize"])  # Độ chính xác giá
            step_size = float(symbol_info["filters"][2]["stepSize"])  # Độ chính xác số lượng
            break

    if tick_size is None or step_size is None:
        logging.error(f"❌ Không lấy được thông tin tickSize hoặc stepSize cho {symbol}")
        return None

    # 🔹 Làm tròn giá đặt lệnh theo tickSize
    price = round(price / tick_size) * tick_size

    # 🔹 Làm tròn số lượng theo stepSize
    quantity = round(quantity / step_size) * step_size
     # **🔥 Tính giá Stop-Loss chính xác**
  
    stop_loss_price = price + (price * (stop_loss_percent / 100) / leverage)
    stop_loss_price = round(stop_loss_price / tick_size) * tick_size  # Làm tròn theo tickSize
  
    # 🔹 Kiểm tra số USDT cần ký quỹ
    required_margin = (quantity * futures_price) / leverage  # Số USDT cần ký quỹ

    if usdt_balance < required_margin:
        logging.warning(f"❌ Không đủ USDT! Cần {required_margin:.2f} USDT nhưng chỉ có {usdt_balance:.2f} USDT.")
        return None  # Không thực hiện lệnh

    logging.info(f"\n📌 Đặt lệnh Limit Short Futures cho {symbol} - Giá: {price}, Số lượng: {quantity}, Đòn bẩy: {leverage}x")

    try:
        order = client_futures.futures_create_order(
            symbol=symbol,
            side="SELL",
            type="LIMIT",
            price=f"{price:.8f}",
            quantity=f"{quantity:.8f}",
            timeInForce="GTC",
            positionSide="SHORT"
        )
        logging.info(f"✅ Lệnh Limit Short thành công! Order ID: {order['orderId']}")
      

        # # Đặt lệnh Stop Market để tự động cắt lỗ
        # logging.info(f"⚠️ Đặt Stop-Loss tại {stop_loss_price:.2f} USDT")
        # stop_order = client_futures.futures_create_order(
        #     symbol=symbol,
        #     side="BUY",
        #     type="STOP_MARKET",
        #     stopPrice=f"{stop_loss_price:.8f}",
        #     quantity=f"{quantity:.8f}",
        #     timeInForce="GTC"
        # )

        # logging.info(f"✅ Stop-Loss thành công! SL Price: {stop_loss_price:.2f} USDT")
        return order 
    except Exception as e:
        logging.error(f"❌ Lỗi khi đặt lệnh Limit Short: {e}")
        return None


# # 🔥 5. Đóng vị thế Long
def close_long_position(symbol, force_take_profit=botConfig.FORCE_TAKE_PROFIT):
    """
    Đóng vị thế Long có lợi nhuận cao nhất trước, hoặc nếu đạt ngưỡng TP cưỡng bức.
    - Hỗ trợ cả One-Way Mode & Hedge Mode.
    
    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param force_take_profit: Lợi nhuận tối thiểu để buộc đóng lệnh (USD)
    """
    print(f"\n📌 Kiểm tra và đóng vị thế Long Futures cho {symbol} nếu có lời")
    
    try:
        # 🔍 1️⃣ Xác định chế độ giao dịch (One-Way Mode hoặc Hedge Mode)
        position_mode = client_futures.futures_get_position_mode()["dualSidePosition"]
        hedge_mode = True if position_mode else False  # True nếu đang dùng Hedge Mode

        # 🔍 2️⃣ Lấy danh sách vị thế đang mở
        active_positions = get_active_trades()
        
        # 🛑 Nếu đang dùng Hedge Mode, chỉ lấy vị thế có positionSide="LONG"
        if hedge_mode:
            long_positions = [pos for pos in active_positions if pos["symbol"] == symbol and pos["positionSide"] == "LONG"]
        else:
            long_positions = [pos for pos in active_positions if pos["symbol"] == symbol and pos["positionAmt"] > 0]

        if not long_positions:
            print(f"⚠️ Không tìm thấy vị thế LONG nào để đóng cho {symbol}")
            return None

        # 🔥 3️⃣ Sắp xếp các vị thế theo lợi nhuận (ưu tiên đóng vị thế lời nhiều nhất trước)
        long_positions.sort(key=lambda x: x["unRealizedProfit"], reverse=True)

        for position in long_positions:
            position_size = abs(float(position["positionAmt"]))
            unrealized_profit = float(position["unRealizedProfit"])
            entry_price = float(position["entryPrice"])
            mark_price = float(position["markPrice"])

            print(f"🔎 Kiểm tra vị thế LONG | Entry: {entry_price:.2f}, Mark: {mark_price:.2f}, Lời/Lỗ: {unrealized_profit:.2f} USD")

            # 🚨 4️⃣ Chỉ đóng lệnh nếu có lời hoặc đạt ngưỡng TP cưỡng bức
            if unrealized_profit >= force_take_profit:
                print(f"✅ Đóng vị thế LONG {symbol} vì đạt lợi nhuận tối thiểu ({force_take_profit} USD)!")
                
                # ✅ 5️⃣ Tạo lệnh đóng vị thế (Tự động hỗ trợ Hedge Mode)
                order_params = {
                    "symbol": symbol,
                    "side": "SELL",
                    "type": "MARKET",
                    "quantity": position_size
               
                }
                
                if hedge_mode:
                    order_params["positionSide"] = "LONG"  # 🔹 Bắt buộc phải có nếu Hedge Mode bật

                order = client_futures.futures_create_order(**order_params)
                
                print(f"✅ Đóng vị thế Long thành công! Order ID: {order['orderId']}")
                return order

        print(f"⚠️ Không có vị thế LONG nào đạt mức lợi nhuận tối thiểu {force_take_profit} USD!")
        return None

    except Exception as e:
        print(f"❌ Lỗi khi đóng vị thế Long: {e}")
        return None


# def close_long_position(symbol):
#     print(f"\n📌 Đóng toàn bộ vị thế Long Futures cho {symbol}")
#     try:
#         order = client_futures.futures_create_order(
#             symbol=symbol,
#             side="SELL",
#             type="MARKET",
#             reduceOnly=True  # Đảm bảo chỉ đóng vị thế, không mở thêm
#         )
#         print(f"✅ Đóng vị thế Long thành công! Order ID: {order['orderId']}")
#         return order
#     except Exception as e:
#         print(f"❌ Lỗi khi đóng vị thế Long: {e}")
#         return None
 

# # 🔥 6. Đóng vị thế Short
def close_short_position(symbol, force_take_profit=botConfig.FORCE_TAKE_PROFIT):
    """
    Đóng vị thế Short có lợi nhuận cao nhất trước, hoặc nếu đạt ngưỡng TP cưỡng bức.
    - Hỗ trợ cả One-Way Mode & Hedge Mode.
    
    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param force_take_profit: Lợi nhuận tối thiểu để buộc đóng lệnh (USD)
    """
    print(f"\n📌 Kiểm tra và đóng vị thế Short Futures cho {symbol} nếu có lời")

    try:
        # 🔍 1️⃣ Xác định chế độ giao dịch (One-Way Mode hoặc Hedge Mode)
        position_mode = client_futures.futures_get_position_mode()["dualSidePosition"]
        hedge_mode = True if position_mode else False  # True nếu đang dùng Hedge Mode

        # 🔍 2️⃣ Lấy danh sách vị thế đang mở
        active_positions = get_active_trades()
        
        # 🛑 Nếu Hedge Mode đang bật, chỉ lấy vị thế có positionSide="SHORT"
        if hedge_mode:
            short_positions = [pos for pos in active_positions if pos["symbol"] == symbol and pos["positionSide"] == "SHORT"]
        else:
            short_positions = [pos for pos in active_positions if pos["symbol"] == symbol and pos["positionAmt"] < 0]

        if not short_positions:
            print(f"⚠️ Không tìm thấy vị thế SHORT nào để đóng cho {symbol}")
            return None

        # 🔥 3️⃣ Sắp xếp vị thế theo lợi nhuận (ưu tiên đóng vị thế lời nhiều nhất trước)
        short_positions.sort(key=lambda x: x["unRealizedProfit"], reverse=True)

        for position in short_positions:
            position_size = abs(float(position["positionAmt"]))
            unrealized_profit = float(position["unRealizedProfit"])
            entry_price = float(position["entryPrice"])
            mark_price = float(position["markPrice"])

            print(f"🔎 Kiểm tra vị thế SHORT | Entry: {entry_price:.2f}, Mark: {mark_price:.2f}, Lời/Lỗ: {unrealized_profit:.2f} USD")

            # 🚨 4️⃣ Chỉ đóng lệnh nếu có lời hoặc đạt ngưỡng TP cưỡng bức
            if unrealized_profit >= force_take_profit:
                print(f"✅ Đóng vị thế SHORT {symbol} vì đạt lợi nhuận tối thiểu ({force_take_profit} USD)!")

                # ✅ 5️⃣ Tạo lệnh đóng vị thế (Hỗ trợ Hedge Mode tự động)
                order_params = {
                    "symbol": symbol,
                    "side": "BUY",
                    "type": "MARKET",
                    "quantity": position_size
                
                }

                if hedge_mode:
                    order_params["positionSide"] = "SHORT"  # 🔹 Bắt buộc nếu Hedge Mode bật

                order = client_futures.futures_create_order(**order_params)

                print(f"✅ Đóng vị thế Short thành công! Order ID: {order['orderId']}")
                return order

        print(f"⚠️ Không có vị thế SHORT nào đạt mức lợi nhuận tối thiểu {force_take_profit} USD!")
        return None

    except Exception as e:
        print(f"❌ Lỗi khi đóng vị thế Short: {e}")
        return None


# def close_short_position(symbol):
#     print(f"\n📌 Đóng toàn bộ vị thế Short Futures cho {symbol}")
#     try:
#         order = client_futures.futures_create_order(
#             symbol=symbol,
#             side="BUY",
#             type="MARKET",
#             reduceOnly=True  # Đảm bảo chỉ đóng vị thế, không mở thêm
#         )
#         print(f"✅ Đóng vị thế Short thành công! Order ID: {order['orderId']}")
#         return order
#     except Exception as e:
#         print(f"❌ Lỗi khi đóng vị thế Short: {e}")
#         return None

# 🔥 7. Kiểm tra số dư USDT trên Futures
def get_futures_balance(asset="USDT"):
    print(f"\n📌 Kiểm tra số dư {asset} trên Futures...")
    try:
        account_info = client_futures.futures_account_balance()
        for balance in account_info:
            if balance["asset"] == asset:
                usdt_balance = float(balance["balance"])
                print(f"💰 Số dư {asset} Futures: {usdt_balance}")
                return usdt_balance
        print(f"❌ Không tìm thấy {asset} trong tài khoản Futures.")
        return 0.0
    except Exception as e:
        print(f"❌ Lỗi khi lấy số dư Futures: {e}")
        return 0.0

 
# 🔥 1. Lấy danh sách giao dịch Futures đang mở
def get_active_trades():
    """
    Lấy danh sách các vị thế đang mở trên Futures.
    """
    try:
        # 🔹 Lấy thông tin vị thế mở
        # positions = client_futures.futures_position_information()
        positions = client_futures.futures_position_information(timestamp=int(time.time() * 1000))
        # print(f"📌 Vị thế Futures đang mở: {positions}")

        active_positions = []
        for pos in positions:
            if float(pos["positionAmt"]) != 0:  # Chỉ lấy các vị thế đang mở
                symbol = pos["symbol"]
                active_positions.append({
                    "symbol": symbol,
                    "positionAmt": float(pos["positionAmt"]),  # Số lượng hợp đồng
                    "entryPrice": float(pos["entryPrice"]),  # Giá vào lệnh
                    "markPrice": float(pos["markPrice"]),  # Giá đánh dấu hiện tại
                    "unRealizedProfit": float(pos["unRealizedProfit"]),  # Lợi nhuận chưa thực hiện
                    "liquidationPrice": float(pos["liquidationPrice"]),  # Giá thanh lý
                    "initialMargin": float(pos["isolatedWallet"]),  # Ký quỹ ban đầu
                    "maintMargin": float(pos["maintMargin"]),  # Ký quỹ duy trì
                    "side": "LONG" if float(pos["positionAmt"]) > 0 else "SHORT",                  
                    "positionSide": pos["positionSide"] # "BOTH" hoặc "LONG" hoặc "SHORT"
                })

        # logging.info(f"🔄 Vị thế đang mở: {active_positions}")
        return active_positions

    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy danh sách giao dịch đang mở: {e}")
        return []


 
def cancel_all_orders(symbol):
    """
    Hủy tất cả các lệnh chờ của một cặp giao dịch Futures.

    :param symbol: Cặp giao dịch Futures (VD: "BTCUSDT")
    """
    try:
        open_orders = client_futures.futures_get_open_orders(symbol=symbol)  # Lấy danh sách lệnh chờ

        if not open_orders:
            logging.info(f"✅ Không có lệnh chờ nào để hủy cho {symbol}.")
            return

        logging.info(f"❌ Đang hủy {len(open_orders)} lệnh chờ của {symbol}...")

        for order in open_orders:
            client_futures.futures_cancel_order(symbol=symbol, orderId=order["orderId"])  # Hủy từng lệnh

        logging.info(f"✅ Đã hủy tất cả lệnh chờ của {symbol}!")

    except Exception as e:
        logging.error(f"❌ Lỗi khi hủy lệnh chờ của {symbol}: {e}")


# 🔥 2. Lấy số lượng lệnh đang mở trên Futures
def get_open_order_count():
    """
    Lấy tổng số lệnh đang mở trên Futures.
    """
    try:
        orders = client_futures.futures_get_open_orders(timestamp=int(time.time() * 1000))
        return len(orders)
    except Exception as e:
        print(f"❌ Lỗi khi lấy số lượng lệnh mở: {e}")
        return 0
def get_open_position_count():
    """
    Đếm tổng số vị thế đang mở trên Futures.
    
    :return: Số lượng vị thế đang mở
    """
    try:
        positions = client_futures.futures_position_information()
        open_positions = [pos for pos in positions if float(pos["positionAmt"]) != 0]
        return len(open_positions)
    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy số vị thế mở: {e}")
        return 0
def get_pending_orders(symbol=None):
    """
    Lấy danh sách các lệnh đang chờ khớp trên Futures.

    :param symbol: Cặp giao dịch cụ thể (VD: BTCUSDT), nếu None sẽ lấy tất cả.
    :return: Danh sách các lệnh chờ khớp
    """
    try:
        if symbol:
            orders = client_futures.futures_get_open_orders(symbol=symbol)
        else:
            orders = client_futures.futures_get_open_orders()
        # print(orders)
       
        pending_orders = [
            {
                "symbol": order["symbol"],
                "orderId": order["orderId"],
                "side": order["side"],
                "price": float(order["price"]),
                "quantity": float(order["origQty"]),
                "status": order["status"],
                "updateTime": order["updateTime"],  # 📌 Thêm updateTime để kiểm tra thời gian treo
                "type": order["type"]
            }
            for order in orders
        ]

        return pending_orders
    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy danh sách lệnh chờ khớp: {e}")
        return []
 
# ✅ Hàm 1: Chỉnh sửa lệnh (Thay vì hủy toàn bộ)
def modify_order(symbol, old_price, side):
    """
    Chỉnh sửa lệnh gần biên lưới nhất thay vì hủy toàn bộ.
    Nếu lệnh xa nhất lệch quá nhiều so với giá hiện tại, bot sẽ cập nhật lại giá.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param old_price: Giá cũ của lệnh
    :param side: "BUY" hoặc "SELL"
    """
    try:
        open_orders = client_futures.futures_get_open_orders(symbol=symbol)

        # 🔹 Lấy thông tin tickSize & stepSize từ Binance
        exchange_info = client_futures.futures_exchange_info()
        tick_size = None
        step_size = None

        for symbol_info in exchange_info["symbols"]:
            if symbol_info["symbol"] == symbol:
                tick_size = float(symbol_info["filters"][0]["tickSize"])  # Độ chính xác giá
                step_size = float(symbol_info["filters"][2]["stepSize"])  # Độ chính xác số lượng
                break

        if tick_size is None or step_size is None:
            logging.error(f"❌ Không lấy được thông tin tickSize hoặc stepSize cho {symbol}")
            return None

        # 🔹 Hàm làm tròn giá theo tick_size
        def round_price(price):
            return round(price / tick_size) * tick_size

        # 🔹 Hàm làm tròn số lượng theo step_size
        def round_quantity(quantity):
            return round(quantity / step_size) * step_size

        # Tìm lệnh xa nhất theo loại giao dịch
        target_order = None
        for order in open_orders:
            if order["side"] == side and float(order["price"]) == old_price:
                target_order = order
                break

        if not target_order:
            logging.warning(f"⚠️ Không tìm thấy lệnh {side} ở giá {old_price}!")
            return

        # 🔹 Lấy giá Futures hiện tại
        futures_price_info = client_futures.futures_mark_price(symbol=symbol)
        futures_price = float(futures_price_info["markPrice"])

        grid_spacing = botConfig.GRID_SPACING_PERCENT / 100
        new_price = (
            futures_price * (1 - grid_spacing) if side == "BUY" else futures_price * (1 + grid_spacing)
        )

        # ✅ **Làm tròn giá theo `tick_size`**
        new_price = round_price(new_price)

        # Nếu giá mới khác đáng kể giá cũ → Hủy & đặt lại
        price_deviation = abs(new_price - old_price) / old_price
        if price_deviation > grid_spacing:
            logging.info(f"🔄 Cập nhật lệnh {side} từ {old_price:.2f} → {new_price:.2f}")
            client_futures.futures_cancel_order(symbol=symbol, orderId=target_order["orderId"])
            time.sleep(1)

            # ✅ **Làm tròn số lượng theo `step_size`**
            quantity = round_quantity(botConfig.GRID_ORDER_VALUE * botConfig.TRADE_LEVERAGE / new_price)

            if side == "BUY":
                client_futures.futures_create_order(
                    symbol=symbol, side="BUY", type="LIMIT", price=new_price, quantity=quantity, timeInForce="GTC"
                )
            else:
                client_futures.futures_create_order(
                    symbol=symbol, side="SELL", type="LIMIT", price=new_price, quantity=quantity, timeInForce="GTC"
                )

            logging.info(f"✅ Đã đặt lại lệnh {side} tại giá {new_price:.2f} | Số lượng: {quantity}")

    except Exception as e:
        logging.error(f"❌ Lỗi khi cập nhật lệnh {side} tại giá {old_price}: {e}")


# ✅ Hàm 2: Lấy danh sách lệnh đã khớp gần nhất
def get_filled_trades(symbol):
    """
    Lấy danh sách các lệnh đã khớp gần đây để bổ sung lệnh mới khi cần.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :return: Danh sách các lệnh đã khớp gần đây (list)
    """
    try:
        filled_trades = []
        recent_trades = client_futures.futures_account_trades(symbol=symbol, limit=10)  # Lấy 10 giao dịch gần nhất

        for trade in recent_trades:
            filled_trades.append({
                "symbol": trade["symbol"],
                "price": float(trade["price"]),
                "quantity": float(trade["qty"]),
                "time": trade["time"],
                "side": "BUY" if trade["buyer"] else "SELL"  # Binance không trả về "side", cần tự xác định
            })

        logging.info(f"🔍 Lệnh đã khớp gần đây: {filled_trades}")
        return filled_trades

    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy danh sách lệnh đã khớp: {e}")
        return []
 
def cancel_order_orderId(symbol, order_id):
    """
    Hủy một lệnh đang chờ khớp trên Futures theo orderId.

    :param symbol: Cặp giao dịch Futures (VD: BTCUSDT)
    :param order_id: ID của lệnh cần hủy
    """
    try:
        response = client_futures.futures_cancel_order(symbol=symbol, orderId=order_id)
        logging.info(f"✅ Đã hủy lệnh {order_id} của {symbol}. Trạng thái: {response}")
        return response
    except Exception as e:
        logging.error(f"❌ Lỗi khi hủy lệnh {order_id} của {symbol}: {e}")
        return None
import time
import datetime
import logging

 

def summary_profit(symbol="BTCUSDT"):
    try:
        trades = client_futures.futures_account_trades(symbol=symbol, limit=999)
        income_history = client_futures.futures_income_history(symbol=symbol, incomeType="FUNDING_FEE", limit=999)
        open_orders = get_open_order_count()
        active_positions = get_active_trades()
        open_positions_count = len(active_positions)
        if not trades:
            print("\n⚠️ Không có giao dịch nào để tổng hợp lợi nhuận!\n")
            return

        total_realized_pnl = 0.0
        total_commission = 0.0
        total_funding_fee = 0.0
        buy_trades = 0
        sell_trades = 0
        win_trades = 0
        loss_trades = 0
        liquidation_count = 0

        first_trade_time = trades[0]["time"]
        last_trade_time = trades[-1]["time"]

        for trade in trades:
            pnl = float(trade["realizedPnl"])
            commission = float(trade["commission"])
            total_realized_pnl += pnl
            total_commission += commission
            if trade["side"] == "BUY":
                buy_trades += 1
            elif trade["side"] == "SELL":
                sell_trades += 1
            if pnl > 0:
                win_trades += 1
            elif pnl < 0:
                loss_trades += 1
            if "liquidation" in trade and trade["liquidation"]:
                liquidation_count += 1

        for income in income_history:
            total_funding_fee += float(income["income"])  # Âm nếu trả, dương nếu nhận

        print("\n" + "="*60+"\n")
        logging.info(f"🔄 Số lệnh mở: {open_orders} | Số vị thế mở: {open_positions_count}")
        print("\n" + "="*60)
        print(f"📊 **TỔNG KẾT LỢI NHUẬN (999 giao dịch gần nhất) ** 📊")
        print("="*60)
        print(f"📅 Giao dịch đầu tiên: {datetime.datetime.fromtimestamp(first_trade_time / 1000, datetime.UTC)} UTC")
        print(f"📅 Giao dịch cuối cùng: {datetime.datetime.fromtimestamp(last_trade_time / 1000, datetime.UTC)} UTC")
        print(f"✅ Tổng số giao dịch: {buy_trades + sell_trades} (BUY: {buy_trades}, SELL: {sell_trades})")
        print(f"🏆 Lệnh thắng: {win_trades} | ❌ Lệnh thua: {loss_trades}")
        print(f"⚠️ Số lần bị thanh lý: {liquidation_count}")
        print(f"💰 Tổng lợi nhuận (PnL): {total_realized_pnl:.2f} USDT")
        print(f"💸 Tổng phí giao dịch (Maker/Taker): {total_commission:.2f} USDT")
        print(f"💸 Tổng phí Funding: {total_funding_fee:.2f} USDT")
        print(f"⚖️ Lợi nhuận ròng (sau phí): {total_realized_pnl - total_commission - total_funding_fee:.2f} USDT")
        print("="*60 + "\n")

    except Exception as e:
        logging.error(f"❌ Lỗi khi lấy tổng hợp lợi nhuận: {e}")
  
# def set_tp_sl_for_position(symbol):
#     """
#     Đặt hoặc cập nhật TP/SL dựa trên margin thực tế.
#     - Lấy thông tin từ active_positions để kiểm tra margin.
#     - Kiểm tra xem lệnh TP/SL hiện tại có đúng margin không.
#     - Nếu margin khác nhau, hủy lệnh TP/SL cũ và đặt lại.
#     """
#     try:
#         # 🚀 Lấy thông tin vị thế mở từ active_positions
#         active_positions = get_active_trades()
#         position = next((pos for pos in active_positions if pos["symbol"] == symbol), None)
#         # ✅ Lấy danh sách lệnh TP/SL hiện tại
#         open_orders = client_futures.futures_get_open_orders(symbol=symbol)

#         existing_tp = next((order for order in open_orders if order["type"] == "TAKE_PROFIT_MARKET"), None)
#         existing_sl = next((order for order in open_orders if order["type"] == "STOP_MARKET"), None)

#         # 🚀 **CASE 1: Không có vị thế nhưng vẫn còn TP/SL → Hủy lệnh**
#         if not position or float(position["positionAmt"]) == 0:
#             if existing_tp or existing_sl:
#                 logging.warning(f"⚠️ Không có vị thế mở nhưng vẫn còn TP/SL! Hủy lệnh cho {symbol}.")
#                 if existing_tp:
#                     client_futures.futures_cancel_order(symbol=symbol, orderId=existing_tp["orderId"])
#                     logging.info(f"🛑 Đã hủy TP: {existing_tp['orderId']}")

#                 if existing_sl:
#                     client_futures.futures_cancel_order(symbol=symbol, orderId=existing_sl["orderId"])
#                     logging.info(f"🛑 Đã hủy SL: {existing_sl['orderId']}")
#             return  # Thoát ngay, không cần tiếp tục đặt TP/SL mới

#         position_size = abs(float(position["positionAmt"]))  # Luôn lấy giá trị tuyệt đối
#         entry_price = float(position["entryPrice"])
#         current_margin = float(position["initialMargin"])  # Số vốn margin thực tế
#         margin_in_qty = current_margin / entry_price  # Chuyển USDT → Coin
#         mark_price = float(position["markPrice"])  # Lấy giá đánh dấu hiện tại


#         # ✅ Lấy thông tin tickSize, stepSize & minQty từ Binance
#         exchange_info = client_futures.futures_exchange_info()
#         tick_size = step_size = min_qty = None

#         for symbol_info in exchange_info["symbols"]:
#             if symbol_info["symbol"] == symbol:
#                 tick_size = float(symbol_info["filters"][0]["tickSize"])  # Độ chính xác giá
#                 step_size = float(symbol_info["filters"][2]["stepSize"])  # Độ chính xác số lượng
#                 min_qty = float(symbol_info["filters"][2]["minQty"])  # Số lượng tối thiểu
#                 break

#         if not tick_size or not step_size or not min_qty:
#             logging.error(f"❌ Không lấy được thông tin tickSize, stepSize hoặc minQty cho {symbol}")
#             return

#         # ✅ Tính toán Take Profit (TP) & Stop Loss (SL) dựa trên margin
#         tp_profit = current_margin * (botConfig.TP_PERCENT / 100)  # Lợi nhuận TP dựa trên margin
#         sl_loss = current_margin * (botConfig.SL_PERCENT / 100)  # Lỗ tối đa SL dựa trên margin

#         tp_price = entry_price + (tp_profit / position_size) if float(position["positionAmt"]) > 0 else entry_price - (tp_profit / position_size)
#         sl_price = entry_price - (sl_loss / position_size) if float(position["positionAmt"]) > 0 else entry_price + (sl_loss / position_size)
        
#          # ✅ Tính toán mức trailing stop động
#         if position_size > 0:  # LONG Position
#             profit_threshold_1 = entry_price * 1.05  # +5% từ entry
#             profit_threshold_2 = entry_price * 1.10  # +10% từ entry
#             if mark_price >= profit_threshold_2:
#                 sl_price = entry_price * 1.03  # Tăng SL lên entry + 3% lợi nhuận
#             elif mark_price >= profit_threshold_1:
#                 sl_price = entry_price  # SL về entry price (hòa vốn)
#         else:  # SHORT Position
#             profit_threshold_1 = entry_price * 0.95  # -5% từ entry
#             profit_threshold_2 = entry_price * 0.90  # -10% từ entry
#             if mark_price <= profit_threshold_2:
#                 sl_price = entry_price * 0.97  # Dời SL xuống entry - 3% lợi nhuận
#             elif mark_price <= profit_threshold_1:
#                 sl_price = entry_price  # SL về entry price (hòa vốn)


#         # 🔥 Làm tròn giá theo tick_size
#         tp_price = round(tp_price / tick_size) * tick_size
#         sl_price = round(sl_price / tick_size) * tick_size

#         # 🔥 Làm tròn số lượng theo step_size và đảm bảo >= minQty
#         quantity = max(min_qty, round(position_size / step_size) * step_size)

       
        
#         # ✅ Kiểm tra xem margin của TP/SL có đúng không    
#         if existing_tp:
#             tp_margin = float(existing_tp["origQty"])
#             if abs(tp_margin - margin_in_qty) > 1.0:
#                 logging.info(f"🛑 Hủy TP cũ: {existing_tp['orderId']} vì margin thay đổi!")
#                 response = client_futures.futures_cancel_order(symbol=symbol, orderId=existing_tp["orderId"])
#                 if response and response["status"] == "CANCELED":
#                     existing_tp = None  # Chỉ đặt None nếu đã hủy thành công

#         if existing_sl:
#             sl_margin = float(existing_sl["origQty"])
#             if abs(sl_margin - margin_in_qty) > 1.0:
#                 logging.info(f"🛑 Hủy SL cũ: {existing_sl['orderId']} vì margin thay đổi!")
#                 response = client_futures.futures_cancel_order(symbol=symbol, orderId=existing_sl["orderId"])
#                 if response and response["status"] == "CANCELED":
#                     existing_sl = None  # Chị đặt None nếu hàng hủy thành cong             


       


#         # 🚀 Đặt lệnh TP mới nếu cần
#         if not existing_tp:
#             client_futures.futures_create_order(
#                 symbol=symbol,
#                 side="SELL" if float(position["positionAmt"]) > 0 else "BUY",
#                 type="TAKE_PROFIT_MARKET",
#                 stopPrice=f"{tp_price:.8f}",  # Định dạng giá chính xác
#                 quantity=f"{quantity:.8f}",  # Định dạng số lượng chính xác
#                 timeInForce="GTC",
#                 reduceOnly=True
#             )
#             logging.info(f"✅ Đã đặt TP tại {tp_price:.8f} cho {symbol} (Size: {quantity})")

#         # 🚀 Đặt lệnh SL mới nếu cần
#         if not existing_sl:
#             client_futures.futures_create_order(
#                 symbol=symbol,
#                 side="SELL" if float(position["positionAmt"]) > 0 else "BUY",
#                 type="STOP_MARKET",
#                 stopPrice=f"{sl_price:.8f}",  # Định dạng giá chính xác
#                 quantity=f"{quantity:.8f}",  # Định dạng số lượng chính xác
#                 timeInForce="GTC",
#                 reduceOnly=True
#             )
#             logging.info(f"✅ Đã đặt SL tại {sl_price:.8f} cho {symbol} (Size: {quantity})")

#     except Exception as e:
#         logging.error(f"❌ Lỗi khi đặt TP/SL: {e}")

def set_tp_sl_for_positions_for_multi_open_positions(symbol):
    """
    Đặt hoặc cập nhật TP/SL cho từng vị thế mở của một symbol.
    - Hỗ trợ nhiều vị thế cùng lúc.
    - Hủy TP/SL cũ nếu margin thay đổi.
    - Loại bỏ TP/SL trùng lặp, giữ lại 1 cặp duy nhất.
    """
    logging.info(f"🚀 Khởi động tiến trình kiểm tra Stop/Loss cho vị thế")
    try:
        # 🚀 Lấy toàn bộ vị thế mở từ active_positions
        active_positions = get_active_trades()
        positions = [pos for pos in active_positions if pos["symbol"] == symbol]

        # ✅ Lấy danh sách lệnh TP/SL hiện tại
        open_orders = client_futures.futures_get_open_orders(symbol=symbol)
        tp_orders = {order["orderId"]: order for order in open_orders if order["type"] == "TAKE_PROFIT_MARKET"}
        sl_orders = {order["orderId"]: order for order in open_orders if order["type"] == "STOP_MARKET"}

        # 🚀 **CASE 1: Nếu không có vị thế mở nhưng có TP/SL → Hủy tất cả TP/SL cũ**
        if not positions:
            if tp_orders or sl_orders:
                logging.warning(f"⚠️ Không có vị thế mở nhưng vẫn còn TP/SL! Hủy toàn bộ lệnh cho {symbol}.")
                for order_id in list(tp_orders.keys()) + list(sl_orders.keys()):
                    client_futures.futures_cancel_order(symbol=symbol, orderId=order_id)
                    logging.info(f"🛑 Đã hủy lệnh TP/SL: {order_id}")
            return

        # ✅ Lấy thông tin tickSize, stepSize & minQty từ Binance
        exchange_info = client_futures.futures_exchange_info()
        symbol_info = next((s for s in exchange_info["symbols"] if s["symbol"] == symbol), None)

        if not symbol_info:
            logging.error(f"❌ Không lấy được thông tin symbol {symbol}")
            return
        # ✅ Kiểm tra chế độ Hedge Mode
        position_mode = client_futures.futures_get_position_mode()["dualSidePosition"]
        hedge_mode = True if position_mode else False
        tick_size = float(symbol_info["filters"][0]["tickSize"])
        step_size = float(symbol_info["filters"][2]["stepSize"])
        min_qty = float(symbol_info["filters"][2]["minQty"])
        if hedge_mode:
            for position in positions:

                position_size = abs(float(position["positionAmt"]))
                position_side = position["positionSide"]  # "LONG" hoặc "SHORT"
                entry_price = float(position["entryPrice"])
                mark_price = float(position["markPrice"])
                current_margin = float(position["initialMargin"])
                

                # ✅ Tính toán Take Profit (TP) & Stop Loss (SL)
                
                if position_side == "LONG":
                    tp_price = entry_price + (current_margin * (botConfig.TP_PERCENT / 100)) / position_size
                    sl_price = entry_price - (current_margin * (botConfig.SL_PERCENT / 100)) / position_size
                else:  # SHORT position
                    tp_price = entry_price - (current_margin * (botConfig.TP_PERCENT / 100)) / position_size
                    sl_price = entry_price + (current_margin * (botConfig.SL_PERCENT / 100)) / position_size

                
               
                # 🔥 **Làm tròn giá TP/SL theo tick_size**
                tp_price = round(tp_price / tick_size) * tick_size
                sl_price = round(sl_price / tick_size) * tick_size
                quantity = max(min_qty, round(position_size / step_size) * step_size)
      


                # 🔥 **Kiểm tra nếu TP/SL hiện tại đã tồn tại và đúng margin**
                tp_to_cancel = []
                sl_to_cancel = []
                existing_tp = None
                existing_sl = None

                for order in tp_orders.values():
                    if abs(float(order["origQty"]) - position_size) < 1.0 and order.get("positionSide") == position_side:
                        if existing_tp:
                            tp_to_cancel.append(order["orderId"])
                        else:
                            existing_tp = order  

                for order in sl_orders.values():
                    if abs(float(order["origQty"]) - position_size) < 1.0 and order.get("positionSide") == position_side:
                        if existing_sl:
                            sl_to_cancel.append(order["orderId"])
                        else:
                            existing_sl = order  

                # 🚀 **Hủy TP/SL trùng lặp**
                for order_id in tp_to_cancel + sl_to_cancel:
                    logging.info(f"🛑 Hủy lệnh TP/SL trùng: {order_id}")
                    client_futures.futures_cancel_order(symbol=symbol, orderId=order_id)
                
                # Làm mới danh sách lệnh sau khi hủy
                open_orders = client_futures.futures_get_open_orders(symbol=symbol)
                tp_orders = {order["orderId"]: order for order in open_orders if order["type"] == "TAKE_PROFIT_MARKET"}
                sl_orders = {order["orderId"]: order for order in open_orders if order["type"] == "STOP_MARKET"}
                existing_tp = next((order for order in tp_orders.values() if order.get("positionSide") == position_side), None)
                existing_sl = next((order for order in sl_orders.values() if order.get("positionSide") == position_side), None)



                if existing_tp:
                    tp_margin = float(existing_tp["origQty"])
                    tp_position_side = existing_tp.get("positionSide")  # Xác định TP của Long hay Short
                    position_tp = next((p for p in positions if p["positionSide"] == tp_position_side), None)

                    if position_tp:
                        margin_in_qty = abs(float(position_tp["positionAmt"]))
                        if abs(tp_margin - margin_in_qty) > 1.0:
                            logging.info(f"🛑 Hủy TP cũ: {existing_tp['orderId']} (Side: {tp_position_side}) vì margin thay đổi!")
                            response = client_futures.futures_cancel_order(symbol=symbol, orderId=existing_tp["orderId"])
                            if response and response["status"] == "CANCELED":
                                existing_tp = None  # Chỉ đặt None nếu đã hủy thành công

                if existing_sl:
                    sl_margin = float(existing_sl["origQty"])
                    sl_position_side = existing_sl.get("positionSide")  # Xác định SL của Long hay Short
                    position_sl = next((p for p in positions if p["positionSide"] == sl_position_side), None)

                    if position_sl:
                        margin_in_qty = abs(float(position_sl["positionAmt"]))
                        if abs(sl_margin - margin_in_qty) > 1.0:
                            logging.info(f"🛑 Hủy SL cũ: {existing_sl['orderId']} (Side: {sl_position_side}) vì margin thay đổi!")
                            response = client_futures.futures_cancel_order(symbol=symbol, orderId=existing_sl["orderId"])
                            if response and response["status"] == "CANCELED":
                                existing_sl = None  # Chỉ đặt None nếu đã hủy thành công
                
                # 🚀 **Đặt TP/SL mới nếu cần**
                if not existing_tp:
                    client_futures.futures_create_order(
                        symbol=symbol,
                        side="SELL" if position_side == "LONG" else "BUY",
                        type="TAKE_PROFIT_MARKET",
                        stopPrice=f"{tp_price:.8f}",
                        quantity=f"{quantity:.8f}",
                        timeInForce="GTC",
                        positionSide=position_side
                    )
                    logging.info(f"✅ Đã đặt TP cho {position_side} tại {tp_price:.8f}")

                if not existing_sl:
                    client_futures.futures_create_order(
                        symbol=symbol,
                        side="SELL" if position_side == "LONG" else "BUY",
                        type="STOP_MARKET",
                        stopPrice=f"{sl_price:.8f}",
                        quantity=f"{quantity:.8f}",
                        timeInForce="GTC",
                        positionSide=position_side
                    )
                    logging.info(f"✅ Đã đặt SL cho {position_side} tại {sl_price:.8f}")
        else:
            # ✅ Xử lý từng vị thế một
            for position in positions:
                position_size = abs(float(position["positionAmt"]))
                entry_price = float(position["entryPrice"])
                mark_price = float(position["markPrice"])
                current_margin = float(position["initialMargin"])  # Lấy margin thực tế
                position_side = "LONG" if float(position["positionAmt"]) > 0 else "SHORT"

                if position_size == 0:
                    logging.warning(f"⚠️ Vị thế {symbol} có position_size = 0, bỏ qua TP/SL!")
                    continue

                # ✅ Tính toán Take Profit (TP) & Stop Loss (SL)
            

                if position_side == "LONG":
                    tp_price = entry_price + (current_margin * (botConfig.TP_PERCENT / 100)) / position_size
                    sl_price = entry_price - (current_margin * (botConfig.SL_PERCENT / 100)) / position_size
                else:  # SHORT position
                    tp_price = entry_price - (current_margin * (botConfig.TP_PERCENT / 100)) / position_size
                    sl_price = entry_price + (current_margin * (botConfig.SL_PERCENT / 100)) / position_size


             

                # 🔥 **Làm tròn giá TP/SL theo tick_size**
                tp_price = round(tp_price / tick_size) * tick_size
                sl_price = round(sl_price / tick_size) * tick_size
                quantity = max(min_qty, round(position_size / step_size) * step_size)


                
                # ✅ Kiểm tra nếu TP/SL hiện tại đã tồn tại và đúng margin
                tp_to_cancel = []
                sl_to_cancel = []
                existing_tp = None
                existing_sl = None

                for order in tp_orders.values():
                    if abs(float(order["origQty"]) - position_size) < 1.0:
                        if existing_tp:  # Nếu đã có TP hợp lệ, thêm order này vào danh sách hủy
                            tp_to_cancel.append(order["orderId"])
                        else:
                            existing_tp = order  # Giữ lại 1 TP hợp lệ

                for order in sl_orders.values():
                    if abs(float(order["origQty"]) - position_size) < 1.0:
                        if existing_sl:  # Nếu đã có SL hợp lệ, thêm order này vào danh sách hủy
                            sl_to_cancel.append(order["orderId"])
                        else:
                            existing_sl = order  # Giữ lại 1 SL hợp lệ

                # 🚀 Hủy TP cũ nếu cần
                if tp_to_cancel:
                    for order_id in tp_to_cancel:
                        logging.info(f"🛑 Hủy TP trùng: {order_id}")
                        client_futures.futures_cancel_order(symbol=symbol, orderId=order_id)
                        

                # 🚀 Hủy SL cũ nếu cần
                if sl_to_cancel:
                    for order_id in sl_to_cancel:
                        logging.info(f"🛑 Hủy SL trùng: {order_id}")
                        client_futures.futures_cancel_order(symbol=symbol, orderId=order_id)
                
                if tp_to_cancel or sl_to_cancel:
                    time.sleep(0.5)
                    continue #Thoát khỏi vòng này, lần sau kiểm tra lại vụ margin
                

                # ✅ **Kiểm tra nếu TP/SL hiện tại đã tồn tại và đúng margin**
                # Làm mới danh sách lệnh sau khi hủy
                open_orders = client_futures.futures_get_open_orders(symbol=symbol)
                tp_orders = {order["orderId"]: order for order in open_orders if order["type"] == "TAKE_PROFIT_MARKET"}
                sl_orders = {order["orderId"]: order for order in open_orders if order["type"] == "STOP_MARKET"}
                existing_tp = next((order for order in tp_orders.values() if abs(float(order["origQty"]) - position_size) < 1.0), None)
                existing_sl = next((order for order in sl_orders.values() if abs(float(order["origQty"]) - position_size) < 1.0), None)

                # 🚀 **Hủy TP cũ nếu cần**
                if existing_tp and abs(float(existing_tp["origQty"]) - position_size) > 1.0:
                    logging.info(f"🛑 Hủy TP cũ {existing_tp['orderId']} do margin thay đổi!")
                    client_futures.futures_cancel_order(symbol=symbol, orderId=existing_tp["orderId"])
                    existing_tp = None  # Đánh dấu cần đặt lại TP

                # 🚀 **Hủy SL cũ nếu cần**
                if existing_sl and abs(float(existing_sl["origQty"]) - position_size) > 1.0:
                    logging.info(f"🛑 Hủy SL cũ {existing_sl['orderId']} do margin thay đổi!")
                    client_futures.futures_cancel_order(symbol=symbol, orderId=existing_sl["orderId"])
                    existing_sl = None  # Đánh dấu cần đặt lại SL
              
                # 🚀 **Đặt TP/SL mới nếu cần**

                
                 
                if not existing_tp:
                    client_futures.futures_create_order(
                        symbol=symbol,
                        side="SELL" if position_side == "LONG" else "BUY",
                        type="TAKE_PROFIT_MARKET",
                        stopPrice=f"{tp_price:.8f}",
                        quantity=f"{quantity:.8f}",
                        timeInForce="GTC",
                         
                    )
                    logging.info(f"✅ Đã đặt TP tại {tp_price:.8f} cho {symbol} (Size: {quantity})")

                if not existing_sl:
                    client_futures.futures_create_order(
                        symbol=symbol,
                        side="SELL" if position_side == "LONG" else "BUY",
                        type="STOP_MARKET",
                        stopPrice=f"{sl_price:.8f}",
                        quantity=f"{quantity:.8f}",
                        timeInForce="GTC")
                       
                logging.info(f"✅ Đã đặt SL tại {sl_price:.8f} cho {symbol} (Size: {quantity})")

    except Exception as e:
        logging.error(f"❌ Lỗi khi đặt TP/SL: {e}")


def close_all_positions():
    """
    Đóng tất cả các vị thế đang mở trên Binance Futures.
    """
    try:
        # ✅ Lấy danh sách tất cả vị thế mở
        active_positions = get_active_trades()
        
        if not active_positions:
            logging.info("✅ Không có vị thế nào đang mở để đóng.")
            return
        
        logging.info(f"🚀 Bắt đầu đóng tất cả {len(active_positions)} vị thế...")

        for position in active_positions:
            symbol = position["symbol"]
            position_size = abs(float(position["positionAmt"]))
            position_side = position["positionSide"]  # "LONG" hoặc "SHORT"

            if position_size == 0:
                continue  # Không có vị thế để đóng

            logging.info(f"🔹 Đang đóng vị thế {position_side} {symbol} (Size: {position_size})")

            # 🔥 Gửi lệnh đóng vị thế
            order = client_futures.futures_create_order(
                symbol=symbol,
                side="SELL" if position_side == "LONG" else "BUY",
                type="MARKET",
                quantity=position_size,
                positionSide=position_side,
                
            )          
            logging.info(f"✅ Đã đóng {position_side} {symbol} | Order ID: {order['orderId']}")
            time.sleep(1)
 

    except Exception as e:
        logging.error(f"❌ Lỗi khi đóng tất cả vị thế: {e}")
       

# 🔥 Gọi hàm này khi cần đóng tất cả vị thế:




if __name__ == "__main__":
    symbol = config.TRADE_PAIR_FUTURES_BTCUSDT
    quantity = 0.01  # Ví dụ: Mở vị thế với 0.01 BTC
    price = 30000  # Giá giả định

    # # Đặt lệnh Market Long
    # get_active_trades()
    # # Kiểm tra số dư USDT
    # get_futures_balance("USDT")
    cancel_all_orders(symbol)
    # print(get_pending_orders(symbol))
    # cancel_order_orderId(symbol, 4087849763)
    # # Lấy lịch sử giao dịch Futures (Gọi từ `check_trade_history_future.py`)
    # summary_profit(symbol)
    # print(get_active_trades())
    # set_tp_sl_for_positions_for_multi_open_positions("BTCUSDT")
    # close_all_positions() 
