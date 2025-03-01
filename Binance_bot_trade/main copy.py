import time
import logging
import os
from Binance_bot_trade.config import botConfig
from Binance_bot_trade.actionBot import strategyChoose, action_spot, action_futures
from Binance_bot_trade.analysis import update_price, check_trade_history_spot, check_trade_history_future
from Binance_bot_trade.utils import logger


def check_risk_management():
    """ Kiểm tra số lần thua liên tiếp & lỗ trong ngày trên cả Spot & Futures. Nếu vượt ngưỡng sẽ dừng bot. """
    
    # Lấy số dư USDT hiện tại trên Spot & Futures
    spot_balance = action_spot.get_spot_balance("USDT")
    futures_balance = action_futures.get_futures_balance("USDT")
    
    initial_balance = botConfig.START_BALANCE  # Vốn khởi điểm

    # Tính % lỗ trong ngày
    spot_loss = ((initial_balance - spot_balance) / initial_balance) * 100 if spot_balance else 0
    futures_loss = ((initial_balance - futures_balance) / initial_balance) * 100 if futures_balance else 0
    total_loss = spot_loss + futures_loss  # Tổng % lỗ

    # 1️⃣ Kiểm tra nếu tổng lỗ trong ngày vượt `DAILY_MAX_LOSS`
    if total_loss >= botConfig.DAILY_MAX_LOSS:
        logging.critical(f"❌ Bot đã lỗ {total_loss:.2f}% trong ngày! DỪNG giao dịch ngay!")
        return False  # Ngừng giao dịch

    # # 2️⃣ Kiểm tra số lần thua liên tiếp
    # if logger.get_consecutive_losses() >= botConfig.MAX_CONSECUTIVE_LOSSES:
    #     logging.warning(f"⚠️ Bot đã thua {botConfig.MAX_CONSECUTIVE_LOSSES} lệnh liên tiếp! TẠM DỪNG giao dịch 1 giờ!")
    #     time.sleep(3600)  # Tạm dừng 1 giờ
    #     logger.reset_consecutive_losses()  # Reset lại số lần thua liên tiếp

    return True  # Cho phép tiếp tục giao dịch


def main():
    logging.info("🚀 BẮT ĐẦU CHẠY BOT TRADING...\n")
    
    # 🔥 Bước 1: Load cấu hình bot
    logging.info("🔹 Đang tải cấu hình từ botConfig.py...")
    trade_mode = botConfig.TRADE_MODE
    test_mode = botConfig.TEST_MODE
    logging.info(f"🔹 Trade Mode: {trade_mode} | Test Mode: {test_mode}")

    while True:
        try:
            logging.info("\n🔍 Kiểm tra trạng thái giao dịch...\n")
            
            # 🔥 Bước 2: Cập nhật giá thị trường
            market_prices = update_price.update_prices()
            if not market_prices or not market_prices.get("spot") or not market_prices.get("futures"):
                logging.warning("⚠️ Không lấy được dữ liệu giá, bỏ qua vòng lặp này!")
                continue

            logging.info(f"🔹 Giá Spot: {market_prices['spot'].get('spot_price', 'N/A')} | Giá Futures: {market_prices['futures'].get('futures_price', 'N/A')}")

            # 🔥 Bước 3: Chạy chiến lược giao dịch
            logging.info("\n🎯 Đang phân tích chiến lược giao dịch...")
            # chosen_strategies = strategyChoose.choose_strategies(trade_mode)
            chosen_strategies = {
                                    "SPOT": strategyChoose.choose_strategies("SPOT"),
                                    "FUTURES": strategyChoose.choose_strategies("FUTURES")
                                }
            chosen_strategies_futures = chosen_strategies.get("FUTURES")
      
            if not chosen_strategies:
                logging.warning("⚠️ Không có chiến lược phù hợp, bỏ qua vòng lặp này!")
                continue
            

            # 🔥 Bước 4: Kiểm tra lịch sử giao dịch
            logging.info("\n📊 Kiểm tra lịch sử giao dịch...")
            check_trade_history_spot.check_trade_history_spot(botConfig.TRADE_PAIRS["SPOT"][0]) 
            check_trade_history_future.check_trade_history_futures(botConfig.TRADE_PAIRS["FUTURES"][0])

            # 🔥 Bước 5: Quản lý lệnh Spot
            if trade_mode in ["SPOT", "BOTH"] and chosen_strategies.get("SPOT"):
                logging.info("\n⚡ Xử lý giao dịch Spot...")

                symbol = botConfig.TRADE_PAIRS["SPOT"][0]
                usdt_balance = action_spot.get_spot_balance("USDT")
                coin_balance = action_spot.get_spot_balance(symbol.replace("USDT", ""))
                open_orders = action_spot.get_open_order_count(symbol)  # Kiểm tra số lệnh đang mở

                # 🔥 Kiểm tra Risk Management trước khi giao dịch
                if not check_risk_management():
                    continue

                # 🔥 Kiểm tra số lượng lệnh đang mở
                
              
                # Lấy danh sách các lệnh mở từ get_active_trades()
                previous_trades = action_spot.get_active_trades()

                if previous_trades:  # Nếu có lệnh mở
                    for trade in previous_trades:
                        try:
                            symbol = trade["symbol"]
                            order_id = trade["orderId"]
                            buy_price = float(trade["price"])  # Giá mua của lệnh
                            quantity = float(trade["quantity"])  # Số lượng coin

                            # Lấy giá hiện tại của Spot
                            current_price = market_prices["spot"]["spot_price"]
                            price_change = (current_price - buy_price) / buy_price * 100

                            TP_THRESHOLD = botConfig.TAKE_PROFIT_PERCENT
                            SL_THRESHOLD = botConfig.STOP_LOSS_PERCENT

                            if price_change >= TP_THRESHOLD:
                                logging.info(f"✅ Giá tăng {price_change:.2f}% → Đặt Limit Sell để chốt lời!")
                                limit_price = current_price * (1 + botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                                action_spot.place_limit_sell_spot(symbol, limit_price, quantity)

                            elif price_change <= -SL_THRESHOLD:
                                logging.warning(f"⚠️ Giá giảm {price_change:.2f}% → Cắt lỗ!")
                                action_spot.place_market_sell_spot(symbol, quantity)

                        except Exception as e:
                            logging.error(f"❌ Lỗi khi xử lý lệnh {trade['orderId']}: {e}")


                else:
                    # Nếu không có lệnh mở, đặt lệnh theo chiến lược
                    if open_orders >= botConfig.MAX_CONCURRENT_TRADES:
                        logging.warning(f"⚠️ SPOT Đã có {open_orders} lệnh mở! Đạt giới hạn {botConfig.MAX_CONCURRENT_TRADES}, không đặt lệnh mới.")
                    else:
                        current_price = market_prices["spot"]["spot_price"]

                        if "BREAKOUT" in chosen_strategies["SPOT"] and usdt_balance > botConfig.MIN_TRADE_AMOUNT:
                            logging.info("🚀 Kích hoạt chiến lược BREAKOUT → Đặt Limit Buy!")
                            limit_price = current_price * (1 - botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                            action_spot.place_limit_buy_spot(symbol, limit_price, botConfig.TRADE_AMOUNT)

                        elif "MEAN_REVERSION" in chosen_strategies["SPOT"] and coin_balance > 0:
                            logging.info("📉 Kích hoạt chiến lược MEAN_REVERSION → Đặt Limit Sell!")
                            limit_price = current_price * (1 + botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                            action_spot.place_limit_sell_spot(symbol, limit_price, botConfig.TRADE_AMOUNT)

                        elif "ICHIMOKU" in chosen_strategies["SPOT"]:
                            ichimoku_signal = update_price.get_ichimoku_signal(symbol)
                            if ichimoku_signal == "BUY" and usdt_balance > botConfig.MIN_TRADE_AMOUNT:
                                logging.info("🌥️ Kích hoạt chiến lược ICHIMOKU → Đặt Market Buy!")
                                action_spot.place_market_buy_spot(symbol, botConfig.TRADE_AMOUNT)
                            elif ichimoku_signal == "SELL" and coin_balance > 0:
                                logging.info("🌥️ Kích hoạt chiến lược ICHIMOKU → Đặt Market Sell!")
                                action_spot.place_market_sell_spot(symbol, botConfig.TRADE_AMOUNT)

                        elif "GOLDEN_CROSS" in chosen_strategies["SPOT"]:
                            golden_cross_signal = update_price.get_golden_cross_signal(symbol)
                            if golden_cross_signal == "BUY" and usdt_balance > botConfig.MIN_TRADE_AMOUNT:
                                logging.info("🏆 Kích hoạt chiến lược GOLDEN CROSS → Đặt Market Buy!")
                                action_spot.place_market_buy_spot(symbol, botConfig.TRADE_AMOUNT)
                            elif golden_cross_signal == "SELL" and coin_balance > 0:
                                logging.info("🏆 Kích hoạt chiến lược GOLDEN CROSS → Đặt Market Sell!")
                                action_spot.place_market_sell_spot(symbol, botConfig.TRADE_AMOUNT)

                        elif "GRID_TRADING" in chosen_strategies["SPOT"]:
                            grid_buy_price = current_price * (1 - botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                            grid_sell_price = current_price * (1 + botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                            logging.info(f"📊 Kích hoạt chiến lược GRID TRADING → Đặt lệnh Buy {grid_buy_price:.2f} & Sell {grid_sell_price:.2f}!")
                            action_spot.place_limit_buy_spot(symbol, grid_buy_price, botConfig.TRADE_AMOUNT)
                            action_spot.place_limit_sell_spot(symbol, grid_sell_price, botConfig.TRADE_AMOUNT)

                        elif "RSI_MACD" in chosen_strategies["SPOT"]:
                            rsi_value = update_price.get_rsi_value(symbol)
                            macd_info = update_price.get_macd_value(symbol)
                            macd_value = macd_info.get("macd", None)
                            signal_value = macd_info.get("signal", None)

                            if rsi_value < 30 and macd_value > signal_value and usdt_balance > botConfig.MIN_TRADE_AMOUNT:
                                logging.info(f"📊 RSI MACD tín hiệu MUA → Đặt Market Buy!")
                                action_spot.place_market_buy_spot(symbol, botConfig.TRADE_AMOUNT)
                            elif rsi_value > 70 and macd_value < signal_value and coin_balance > 0:
                                logging.info(f"📊 RSI MACD tín hiệu BÁN → Đặt Market Sell!")
                                action_spot.place_market_sell_spot(symbol, botConfig.TRADE_AMOUNT)

                        elif "BOLLINGER_BANDS" in chosen_strategies["SPOT"]:
                            bollinger_signal = update_price.get_bollinger_signal(symbol)
                            if bollinger_signal == "BUY" and usdt_balance > botConfig.MIN_TRADE_AMOUNT:
                                logging.info("📏 Kích hoạt chiến lược BOLLINGER BANDS → Đặt Market Buy!")
                                action_spot.place_market_buy_spot(symbol, botConfig.TRADE_AMOUNT)
                            elif bollinger_signal == "SELL" and coin_balance > 0:
                                logging.info("📏 Kích hoạt chiến lược BOLLINGER BANDS → Đặt Market Sell!")
                                action_spot.place_market_sell_spot(symbol, botConfig.TRADE_AMOUNT)

                        else:
                            logging.info("⚠️ Không có chiến lược giao dịch Spot phù hợp!")


            # 🔥 Bước 6: Quản lý lệnh Futures
            # 
            if trade_mode in ["FUTURES", "BOTH"] and chosen_strategies.get("FUTURES"):
                logging.info("\n⚡ Xử lý giao dịch Futures...")

                symbol = botConfig.TRADE_PAIRS["FUTURES"][0]  # Chọn cặp giao dịch mặc định
                usdt_balance = action_futures.get_futures_balance("USDT")  # Kiểm tra số dư USDT
                leverage = botConfig.TRADE_LEVERAGE  # Lấy đòn bẩy từ botConfig
                open_orders = action_futures.get_open_order_count()  # Kiểm tra số lệnh đang mở

                # 🔥 Kiểm tra Risk Management trước khi giao dịch
                if not check_risk_management():
                    continue

                # 🔥 Kiểm tra số lượng lệnh đang mở
                if open_orders >= botConfig.MAX_CONCURRENT_TRADES:
                    logging.warning(f"⚠️ Đã có {open_orders} lệnh mở! Đạt giới hạn {botConfig.MAX_CONCURRENT_TRADES}, không đặt lệnh mới.")
                    continue

                if usdt_balance < botConfig.MIN_TRADE_AMOUNT:
                    logging.warning("⚠️ Không đủ USDT để giao dịch Futures!")
                else:
                    # Lấy giá thị trường hiện tại
                    futures_price_info = update_price.get_futures_price(symbol)
                    futures_price = futures_price_info["futures_price"]

                    if futures_price is None:
                        logging.warning(f"⚠️ Không lấy được giá {symbol}, bỏ qua giao dịch!")
                    else:
                         
                        # Kiểm tra quản lý rủi ro (chỉ tiếp tục nếu chưa lỗ quá mức)
                        if not check_risk_management():
                            logging.critical("❌ Dừng giao dịch Futures do vi phạm giới hạn rủi ro!")
                        else:
                            (
                                    ohlcv_data, rsi_data, macd_data, atr_data, 
                                    ichimoku_data, golden_cross_data, vwap_data, 
                                    pivot_data, volume_profile_data, bollinger_bands, 
                                    mean_reversion_signal
                                ) = strategyChoose.tech_data_spot("FUTURES")
                            # **🔥 Đặt lệnh tùy theo chiến lược đã chọn**
                            if "BREAKOUT" in chosen_strategies_futures["FUTURES"]:
                                limit_price = futures_price * (1 + botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                                logging.info(f"🚀 BREAKOUT → Đặt lệnh LONG Limit tại {limit_price:.2f} USDT (Leverage {leverage}x)")
                                action_futures.place_limit_long(symbol, limit_price, botConfig.TRADE_AMOUNT)

                            elif "SCALPING" in chosen_strategies_futures["FUTURES"]:
                                limit_price = futures_price * (1 + botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)
                                logging.info(f"⚡ SCALPING → Đặt lệnh LONG Limit tại {limit_price:.2f} USDT (Leverage {leverage}x)")
                                action_futures.place_limit_long(symbol, limit_price, botConfig.TRADE_AMOUNT)

                            elif "GRID_TRADING" in chosen_strategies_futures.get("FUTURES", []):
                                logging.info(f"📊 GRID TRADING → Kích hoạt lưới giao dịch cho {symbol}")

                                current_price = futures_price  # Giá hiện tại trên Futures
                                grid_levels = botConfig.GRID_LEVELS  # Số lượng mức giá trong lưới
                                grid_spacing = botConfig.GRID_SPACING_PERCENT / 100  # Khoảng cách giữa các mức

                                for i in range(grid_levels):
                                    # **Tạo các mức giá LONG (BUY)**
                                    limit_buy_price = current_price * (1 - (i + 1) * grid_spacing)
                                    logging.info(f"📉 Đặt lệnh LONG Limit tại {limit_buy_price:.2f} USDT")
                                    action_futures.place_limit_long(symbol, limit_buy_price, botConfig.TRADE_AMOUNT)

                                    # **Tạo các mức giá SHORT (SELL)**
                                    limit_sell_price = current_price * (1 + (i + 1) * grid_spacing)
                                    logging.info(f"📈 Đặt lệnh SHORT Limit tại {limit_sell_price:.2f} USDT")
                                    action_futures.place_limit_short(symbol, limit_sell_price, botConfig.TRADE_AMOUNT)

                            elif "MARKET_MAKING" in chosen_strategies_futures.get("FUTURES", []):
                                logging.info(f"🏦 MARKET MAKING → Cung cấp thanh khoản cho {symbol}")
                                
                                current_price = futures_price  # Giá hiện tại trên Futures
                                limit_buy_price = current_price * (1 - botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)  # Mua thấp hơn
                                limit_sell_price = current_price * (1 + botConfig.LIMIT_ORDER_PRICE_OFFSET / 100)  # Bán cao hơn

                                logging.info(f"📉 Đặt lệnh LONG Limit tại {limit_buy_price:.2f} USDT")
                                action_futures.place_limit_long(symbol, limit_buy_price, botConfig.TRADE_AMOUNT)

                                logging.info(f"📈 Đặt lệnh SHORT Limit tại {limit_sell_price:.2f} USDT")
                                action_futures.place_limit_short(symbol, limit_sell_price, botConfig.TRADE_AMOUNT)


                            elif "RSI_MACD" in chosen_strategies_futures["FUTURES"]:
                                logging.info(f"📈 RSI_MACD → Kiểm tra xu hướng {symbol}")

                                # Lấy dữ liệu kỹ thuật từ `tech_data_spot`
                                

                                # Kiểm tra nếu dữ liệu RSI hoặc MACD không tồn tại
                                if not rsi_data or not macd_data:
                                    logging.warning(f"⚠️ Không thể lấy dữ liệu RSI hoặc MACD cho {symbol}, bỏ qua giao dịch!")
                                else:
                                    # Lấy giá trị RSI mới nhất
                                    rsi_value = rsi_data[-1]["rsi"] if rsi_data else None

                                    # Lấy giá trị MACD mới nhất
                                    macd_value = macd_data[-1]["macd"] if macd_data else None
                                    signal_value = macd_data[-1]["signal"] if macd_data else None

                                    trade_amount = botConfig.TRADE_AMOUNT
                                    leverage = botConfig.TRADE_LEVERAGE

                                    # **1️⃣ Xác định tín hiệu MUA (LONG)**
                                    if rsi_value is not None and macd_value is not None and signal_value is not None:
                                        if rsi_value < 30 and macd_value > signal_value:
                                            logging.info(f"📊 RSI = {rsi_value}, MACD cắt lên Signal → Đặt lệnh LONG {symbol}")
                                            action_futures.place_limit_long(symbol, futures_price, trade_amount)

                                        # **2️⃣ Xác định tín hiệu BÁN (SHORT)**
                                        elif rsi_value > 70 and macd_value < signal_value:
                                            logging.info(f"📊 RSI = {rsi_value}, MACD cắt xuống Signal → Đặt lệnh SHORT {symbol}")
                                            action_futures.place_limit_short(symbol, futures_price, trade_amount)

                                        else:
                                            logging.info(f"📊 RSI = {rsi_value}, MACD chưa có tín hiệu rõ ràng, chờ tín hiệu tiếp theo.")


                            elif "ICHIMOKU" in chosen_strategies_futures["FUTURES"]:
                                logging.info(f"☁️ ICHIMOKU → Phân tích xu hướng {symbol}")
                                action_futures.ichimoku_trading(symbol, botConfig.TRADE_AMOUNT, leverage)

                            elif "PIVOT_POINTS" in chosen_strategies_futures["FUTURES"]:
                                logging.info(f"📍 PIVOT POINTS → Giao dịch theo các điểm pivot {symbol}")
                                action_futures.pivot_trading(symbol, botConfig.TRADE_AMOUNT, leverage)

                            elif "VWAP" in chosen_strategies_futures["FUTURES"]:
                                logging.info(f"📊 VWAP → Giao dịch theo khối lượng trung bình {symbol}")
                                action_futures.vwap_trading(symbol, botConfig.TRADE_AMOUNT, leverage)

                            elif "VOLUME_PROFILE" in chosen_strategies_futures["FUTURES"]:
                                logging.info(f"📊 VOLUME PROFILE → Kiểm tra khối lượng giao dịch {symbol}")
                                action_futures.volume_profile_trading(symbol, botConfig.TRADE_AMOUNT, leverage)

                            else:
                                logging.info("⚠️ Không có chiến lược giao dịch Futures phù hợp!")
                   

                # 🔥 **Kiểm tra TP/SL để đóng lệnh nếu đạt mức lợi nhuận hoặc lỗ**
                logging.info("\n🔄 Kiểm tra vị thế mở để đóng nếu đạt TP/SL...")
                open_positions = action_futures.get_open_positions(symbol)  # Lấy vị thế mở

                for pos in open_positions:
                    entry_price = float(pos["entryPrice"])
                    position_size = float(pos["positionAmt"])
                    current_price = float(futures_price)

                    take_profit_price = entry_price * (1 + botConfig.TAKE_PROFIT_PERCENT / 100)
                    stop_loss_price = entry_price * (1 - botConfig.STOP_LOSS_PERCENT / 100)

                    if position_size > 0:  # LONG
                        if current_price >= take_profit_price:
                            logging.info(f"✅ TP đạt {take_profit_price:.2f} USDT → Đóng LONG {symbol}")
                            action_futures.close_long_position(symbol)
                        elif current_price <= stop_loss_price:
                            logging.warning(f"❌ SL đạt {stop_loss_price:.2f} USDT → Cắt lỗ LONG {symbol}")
                            action_futures.close_long_position(symbol)

                    elif position_size < 0:  # SHORT
                        if current_price <= take_profit_price:
                            logging.info(f"✅ TP đạt {take_profit_price:.2f} USDT → Đóng SHORT {symbol}")
                            action_futures.close_short_position(symbol)
                        elif current_price >= stop_loss_price:
                            logging.warning(f"❌ SL đạt {stop_loss_price:.2f} USDT → Cắt lỗ SHORT {symbol}")
                            action_futures.close_short_position(symbol)


            # # 🔥 Bước 7: Giám sát & Điều chỉnh
            # logging.info("\n🔄 Kiểm tra lệnh mở & điều chỉnh...")
            # action_spot.monitor_orders()
            # action_futures.monitor_orders()

            # 🔥 Bước 8: Ghi log chiến lược đã sử dụng (Chỉ ghi nếu có chiến lược)
            if chosen_strategies.get("SPOT"):
                logger.save_strategy_history("SPOT", chosen_strategies["SPOT"], market_prices["spot"])
            if chosen_strategies.get("FUTURES"):
                logger.save_strategy_history("FUTURES", chosen_strategies["FUTURES"], market_prices["futures"])

        except Exception as e:
            logging.error(f"❌ Lỗi trong quá trình chạy bot: {e}")

        logging.info("\n⏳ Đợi trước khi chạy vòng tiếp theo...\n")
        time.sleep(botConfig.API_REQUEST_INTERVAL)

if __name__ == "__main__":
    main()
