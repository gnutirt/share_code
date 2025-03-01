

import time
import logging
from Binance_bot_trade.config import botConfig
from Binance_bot_trade.actionBot import action_futures, strategyChoose
from Binance_bot_trade.analysis import snip_futures, update_price
import Binance_bot_trade.utils.sync_time as sync_times
import Binance_bot_trade.utils.logger as logger
import threading
import queue
 

def monitor_positions():
    """Luồng kiểm tra TP/SL & đóng vị thế khi đạt lợi nhuận mong muốn."""
    while True:
        try:
            logging.info("\n🔄 [Monitor] Kiểm tra vị thế mở để cập nhật TP/SL & FORCE_TAKE_PROFIT...\n")

            # ✅ Lấy danh sách vị thế đang mở
            active_positions = action_futures.get_active_trades()
            action_futures.summary_profit()
            symbol = botConfig.TRADE_PAIRS["FUTURES"][0]
            action_futures.set_tp_sl_for_positions_for_multi_open_positions(symbol)  
            if not active_positions:
                time.sleep(botConfig.CHECK_PROFIT_INTERVAL)
                continue
            

            # 🔥 **Bước 1: Adaptive TP dựa trên biến động BTC 24h**
            print("[monitor_positions]🔥 Bước 1: Adaptive TP dựa trên biến động BTC 24h:")
            btc_24h_change = update_price.get_btc_24h_change()
            if btc_24h_change is None:
                adaptive_tp_percent = 5  # Giữ mức mặc định
            if btc_24h_change is not None:
                if btc_24h_change > 10:  # BTC tăng mạnh
                    adaptive_tp_percent = 7
                    logging.info(f"📊 BTC tăng {btc_24h_change:.2f}% trong 24h, tăng TP lên 7%")
                elif btc_24h_change < -10:  # BTC giảm mạnh
                    adaptive_tp_percent = 3
                    logging.info(f"📊 BTC giảm {btc_24h_change:.2f}% trong 24h, giảm TP xuống 3%")
                else:  # Giữ mức TP mặc định
                    adaptive_tp_percent = 5       
            # 🔥 Bước 2: Nhóm vị thế theo symbol và tính tổng lợi nhuận
            print("[monitor_positions]🔥 Bước 2: Nhóm vị thế theo symbol và tính tổng lợi nhuận:")
            positions_by_symbol = {}
            for pos in active_positions:
                symbol = pos["symbol"]
                if symbol not in positions_by_symbol:
                    positions_by_symbol[symbol] = {"LONG": None, "SHORT": None, "total_profit": 0}
                pos_data = {
                    "size": float(pos["positionAmt"]),
                    "profit": float(pos["unRealizedProfit"]),
                    "entry_price": float(pos["entryPrice"]),
                    "mark_price": float(pos["markPrice"])
                }
                if pos_data["size"] > 0:
                    positions_by_symbol[symbol]["LONG"] = pos_data
                else:
                    positions_by_symbol[symbol]["SHORT"] = pos_data
                positions_by_symbol[symbol]["total_profit"] += pos_data["profit"]

            # 🔥 Bước 3: Kiểm tra và đóng vị thế
            # 🚨 Cắt lỗ nhanh nếu lỗ vượt mức chấp nhận
     


            print("[monitor_positions]🔥 Bước 3: Kiểm tra và đóng vị thế:")
            for symbol, pos_data in positions_by_symbol.items():
                total_profit = pos_data["total_profit"]
                long_pos = pos_data["LONG"]
                short_pos = pos_data["SHORT"]
                # position_size = pos_data["size"]
                adaptive_tp_value = botConfig.GRID_ORDER_VALUE * adaptive_tp_percent / 100
                long_profit_percent = 0
                short_profit_percent = 0
                if long_pos:
                    long_profit_percent = ((long_pos["mark_price"] - long_pos["entry_price"]) / long_pos["entry_price"]) * 100
                    profit_long = long_pos["profit"]
                else:
                    profit_long = 0
                if short_pos:
                    short_profit_percent = ((short_pos["entry_price"] - short_pos["mark_price"]) / short_pos["entry_price"]) * 100
                    profit_short = short_pos["profit"]
                else:
                    profit_short = 0               
                   
                print(f"Total_profit: {total_profit:.2f}, profit_long: {profit_long}, profit_short: {profit_short}")

                acceptable_loss = botConfig.ACCEPTABLE_LOSS

                if profit_long < 0 and abs(profit_long) < acceptable_loss:
                    logging.warning(f"⚠️ {symbol} lỗ quá mức {acceptable_loss:.2f} USDT ({botConfig.ACCEPTABLE_LOSS}%), đóng vị thế ngay!")
                    close_order = action_futures.close_long_position(symbol)
                    logger.log_trade_closure(symbol, "LONG", long_pos["entry_price"], long_pos["mark_price"], "ACCEPTABLE_LOSS", long_pos["profit"],long_profit_percent)
                    logging.warning(f"❌ Đóng LONG {symbol} do lỗ quá mức chấp nhận: {profit_long:.2f} USDT")

                if profit_short < 0 and abs(profit_short) < acceptable_loss:
                    logging.warning(f"⚠️ {symbol} lỗ quá mức {acceptable_loss:.2f} USDT ({botConfig.ACCEPTABLE_LOSS}%), đóng vị thế ngay!")
                    close_order = action_futures.close_short_position(symbol)   
                    logger.log_trade_closure(symbol, "SHORT", short_pos["entry_price"], short_pos["mark_price"], "ACCEPTABLE_LOSS", short_pos["profit"],short_profit_percent)
                    logging.warning(f"❌ Đóng SHORT {symbol} do lỗ quá mức chấp nhận: {profit_short:.2f} USDT")
 
                # Tính phần trăm lời/lỗ so với vốn ban đầu
                if long_pos and short_pos:
                    if profit_long > 0 and profit_short > 0:
                        close_long_short_order = action_futures.close_all_positions()    
                        logging.info(f"✅ Lọt khe -  Đóng LONG & SHORT {symbol} (Tổng lãi: {total_profit:.2f} USDT)")
                        # 🔥 Clear toàn bộ lệnh treo để bắt đầu chu trình mới
                        open_orders_list = action_futures.get_pending_orders(symbol)
                        if open_orders_list:
                            action_futures.cancel_all_orders(symbol)
                            time.sleep(30)  # Đợi lệnh hủy hoàn tất
                            logging.info(f"✅ Đã xóa sạch lệnh treo cho {symbol}, sẵn sàng chu trình mới")
                            
                        continue

                
                # ✅ Trường hợp 1: Tổng lợi nhuận đạt ngưỡng → Đóng cả LONG và SHORT + Clear orders
                if total_profit >= botConfig.FORCE_TAKE_PROFIT:
                    if long_pos or short_pos:
                        # Tính phần trăm lời/lỗ
                        
                        close_long_short_order = action_futures.close_all_positions()                     
                        if close_long_short_order:
                            logging.info(f"✅ Đóng LONG & SHORT {symbol} (Tổng lãi: {total_profit:.2f} USDT)")
                            logger.log_trade_closure(symbol, "LONG", long_pos["entry_price"], long_pos["mark_price"], "FORCE_TAKE_PROFIT", long_pos["profit"],long_profit_percent)
                            logger.log_trade_closure(symbol, "SHORT", short_pos["entry_price"], short_pos["mark_price"], "FORCE_TAKE_PROFIT", short_pos["profit"],short_profit_percent)               

                        # 🔥 Clear toàn bộ lệnh treo để bắt đầu chu trình mới
                        open_orders_list = action_futures.get_pending_orders(symbol)
                        if open_orders_list:
                            action_futures.cancel_all_orders(symbol)
                            time.sleep(30)  # Đợi lệnh hủy hoàn tất
                            logging.info(f"✅ Đã xóa sạch lệnh treo cho {symbol}, sẵn sàng chu trình mới")
                            
                        continue

                # ✅ Trường hợp 2: Lợi nhuận riêng lẻ đạt ngưỡng lớn → Đóng vị thế đó
                if long_pos and long_pos["profit"] >= max(botConfig.FORCE_TAKE_PROFIT, adaptive_tp_value * 1.5):
                    # Tính phần trăm lời/lỗ
                    long_profit_percent = 0
                    short_profit_percent = 0
                    if long_pos:
                        long_profit_percent = ((long_pos["mark_price"] - long_pos["entry_price"]) / long_pos["entry_price"]) * 100
                    if short_pos:
                        short_profit_percent = ((short_pos["entry_price"] - short_pos["mark_price"]) / short_pos["entry_price"]) * 100
                    close_order = action_futures.close_long_position(symbol)
                    if close_order:
                        logging.info(f"✅ Đóng LONG {symbol} vì lãi riêng lẻ: {long_pos['profit']:.2f} USDT")
                        logger.log_trade_closure(symbol, "LONG", long_pos["entry_price"], long_pos["mark_price"], "FORCE_TAKE_PROFIT", long_pos["profit"],long_profit_percent)
                
                if short_pos and short_pos["profit"] >= max(botConfig.FORCE_TAKE_PROFIT, adaptive_tp_value * 1.5):
                    close_order = action_futures.close_short_position(symbol)
                    if close_order:
                        logging.info(f"✅ Đóng SHORT {symbol} vì lãi riêng lẻ: {short_pos['profit']:.2f} USDT")
                        logger.log_trade_closure(symbol, "SHORT", short_pos["entry_price"], short_pos["mark_price"], "FORCE_TAKE_PROFIT", short_pos["profit"],short_profit_percent)
      
        except Exception as e:
            logging.error(f"❌ Lỗi trong quá trình kiểm tra TP/SL: {e}")

        time.sleep(botConfig.CHECK_PROFIT_INTERVAL)  # Đợi trước khi kiểm tra lại


def main_loop():
    sync_times.sync_time()
    logging.info("🚀 BẮT ĐẦU CHẠY BOT TRADING...\n")
   

    # 🔥 Bước 1: Load cấu hình bot
    logging.info("🔹 Đang tải cấu hình từ botConfig.py...")
    trade_mode = botConfig.TRADE_MODE
    test_mode = botConfig.TEST_MODE
    logging.info(f"🔹 Trade Mode: {trade_mode} | Test Mode: {test_mode}")
    symbol = botConfig.TRADE_PAIRS["FUTURES"][0]
    
 
    while True:
        try:
 

            logging.info("🚀 KHỞI CHẠY MAIN_LOOPS...\n")
            logging.info("\n🔍 Bước 2: Cập nhật giá thị trường\n")
            # Bước 1: Cập nhật giá thị trường
            # 📊 Phân tích biểu đồ Kline để xác định xu hướng
            kline_1h = snip_futures.get_futures_ohlcv(symbol, interval="1h", limit=100)
            kline_4h = snip_futures.get_futures_ohlcv(symbol, interval="4h", limit=100)

            # 🔍 Kiểm tra dữ liệu Kline có hợp lệ không
            if isinstance(kline_1h, dict) and "error" in kline_1h:
                logging.error(f"❌ Lỗi lấy dữ liệu Kline 1H: {kline_1h['error']}")
                kline_1h = []

            if isinstance(kline_4h, dict) and "error" in kline_4h:
                logging.error(f"❌ Lỗi lấy dữ liệu Kline 4H: {kline_4h['error']}")
                kline_4h = []

            if not kline_1h or not kline_4h:
                logging.error("❌ Không có dữ liệu Kline hợp lệ, bỏ qua phân tích xu hướng!")
            else:
                rsi_1h, ema_1h, macd_1h = snip_futures.analyze_kline(kline_1h) or (None, None, None)
                rsi_4h, ema_4h, macd_4h = snip_futures.analyze_kline(kline_4h) or (None, None, None)

                # 🚀 Xác định xu hướng thị trường
                if None in [rsi_1h, ema_1h, macd_1h, rsi_4h, ema_4h, macd_4h]:
                    logging.warning("⚠️ Không có dữ liệu RSI/EMA/MACD, giữ nguyên lưới!")
                    trend_direction = "NEUTRAL"
                else:
                    if rsi_1h > 70 or rsi_4h > 70 or ema_1h < ema_4h:
                        trend_direction = "DOWN"
                    elif rsi_1h < 30 or rsi_4h < 30 or ema_1h > ema_4h:
                        trend_direction = "UP"
                    else:
                        trend_direction = "NEUTRAL"

                logging.info(f"📊 Xu hướng thị trường: {trend_direction}")

            # 🔥 Bước 2: Cập nhật giá thị trường
            market_prices = update_price.update_prices()
           
            if not market_prices or "futures" not in market_prices:
                logging.warning("⚠️ Không lấy được dữ liệu giá Futures, bỏ qua vòng lặp này!")
                continue

            symbol = botConfig.TRADE_PAIRS["FUTURES"][0]
            futures_price = market_prices["futures"].get("futures_price")
            logging.info(f"🔹 Giá Futures: {futures_price}")

            if futures_price is None:
                logging.warning(f"⚠️ Không lấy được giá {symbol}, bỏ qua giao dịch!")
                continue

            # 🔥 Bước 3: Lấy danh sách vị thế & số lệnh đang mở
            logging.info("\n🔥 Bước 3: Lấy danh sách vị thế & số lệnh đang mở\n")
            usdt_balance = action_futures.get_futures_balance("USDT")
            open_orders = action_futures.get_open_order_count() # Lệnh đang treo
            active_positions = action_futures.get_active_trades() #Lệnh đang mở vị thế
            # ✅ **Chia vị thế thành LONG & SHORT**
            # long_positions = [pos for pos in active_positions if pos["positionSide"] == "LONG"]
            # short_positions = [pos for pos in active_positions if pos["positionSide"] == "SHORT"]

            open_orders_list = action_futures.get_pending_orders(symbol) 
            order_value = botConfig.GRID_ORDER_VALUE
            leverage = botConfig.TRADE_LEVERAGE
            # filled_trades = action_futures.get_filled_trades(symbol)

            # 🔥 Lấy dữ liệu ATR mới nhất
            atr_data = strategyChoose.tech_data_furtures()
            # atr_value = atr_data[-1]["atr"] if atr_data else None
            if not atr_data or atr_data[-1].get("atr") is None:
                logging.warning("⚠️ Không có dữ liệu ATR, bỏ qua Adaptive Grid!")
                atr_value = botConfig.MIN_ATR  # Gán giá trị mặc định
            else:
                atr_value = atr_data[-1]["atr"]
                

            open_positions_count = len(active_positions)
            logging.info(f"🔄 Số lệnh mở: {open_orders} | Số vị thế mở: {open_positions_count}")

       
            if usdt_balance < botConfig.MIN_TRADE_AMOUNT:
                logging.warning("⚠️ Không đủ USDT để giao dịch Futures!")
                continue
            
            # 🔥 Bước 4: Lấy dữ liệu Order Book để tránh đặt lệnh vào vùng thanh khoản thấp
            logging.info("\n🔥 Bước 4: Lấy dữ liệu Order Book để tránh đặt lệnh vào vùng thanh khoản thấp\n")
            order_book = update_price.get_order_book(symbol)
           
            if order_book:
                best_bid = float(order_book["bids"][0][0])  # Ép kiểu float
                best_ask = float(order_book["asks"][0][0]) 
                if best_bid < futures_price < best_ask:
                    logging.info(f"📊 Đặt lệnh trong vùng thanh khoản cao: {best_bid} - {best_ask}")
                else:
                    futures_price = (best_bid + best_ask) / 2 
                    logging.warning(f"⚠️ Giá hiện tại nằm ngoài vùng thanh khoản, điều chỉnh vị trí đặt lệnh. Giá Futures: {futures_price}")
                    

            # 🔥 Bước 5: Kiểm tra lệch giá lưới & Adaptive Grid
            logging.info("\n🔥 Bước 5: Kiểm tra lệch giá lưới & Adaptive Grid\n")
            grid_levels = max(botConfig.GRID_LEVELS, int(botConfig.GRID_LEVELS * (max(atr_value, botConfig.MIN_ATR) / futures_price) * botConfig.ADAPTIVE_GRID_SCALING))
            # grid_spacing = max(atr_value / futures_price, botConfig.GRID_SPACING_PERCENT / 100)     
            atr_smooth = sum(entry["atr"] for entry in atr_data[-botConfig.ATR_SMOOTHING_WINDOW:]) / botConfig.ATR_SMOOTHING_WINDOW             
            atr_change = (atr_value - atr_smooth) / atr_smooth
            if atr_change < -0.50:  # ATR giảm mạnh -> Tăng gấp đôi số lệnh GRID
                grid_levels = min(grid_levels * 2, botConfig.MAX_GRID_LEVELS)
                logging.info(f"📊 ATR giảm mạnh (-50%), tăng số lệnh GRID lên {grid_levels}")

            elif atr_change > 0.50:  # ATR tăng mạnh -> Giảm 1/2 số lệnh GRID
                grid_levels = max(grid_levels // 2, botConfig.MIN_GRID_LEVELS)
                logging.info(f"📊 ATR tăng mạnh (+50%), giảm số lệnh GRID xuống {grid_levels}")
            price_volatility = abs(futures_price - market_prices["futures"].get("previous_close")) / futures_price            
            grid_spacing = max(atr_smooth / futures_price, botConfig.GRID_SPACING_PERCENT / 100) * (1 + price_volatility)
            if trend_direction == "UP":
                grid_spacing *= 0.8  # Lưới chặt hơn để đón xu hướng tăng
            elif trend_direction == "DOWN":
                grid_spacing *= 1.2  # Lưới rộng hơn để tránh bắt dao rơi
            grid_spacing = grid_spacing/10
            price_deviation_threshold = grid_levels * grid_spacing*10 #Chia 20 nen phai * 20 lai
            logging.info(f"📊 Adaptive Grid: {grid_levels} → {grid_spacing} (Dựa trên ATR)")


 

            logging.info("\n🔥 Tính toán tâm lưới cải tiến\n")
            grid_center_price = determine_grid_center(
                futures_price=futures_price,
                active_positions=active_positions,
                open_orders_list=open_orders_list,
                order_book=order_book,
                atr_data=atr_data,
                trend_direction=trend_direction
            )
            price_deviation = abs(grid_center_price - futures_price) / futures_price
            logging.info(f"📊 Tâm lưới mới: {grid_center_price:.8f} (Lệch: {price_deviation:.2%})")
          
 

            # 🔥 Kiểm tra lệch giá lưới
            if price_deviation > price_deviation_threshold:
                logging.warning(f"⚠️ Tâm lưới lệch {price_deviation:.2%}, chỉ hủy lệnh GRID và đặt lại!")

                # 🚀 Lấy danh sách lệnh mở
                open_orders_list = action_futures.get_pending_orders(symbol)

                for order in open_orders_list:
                    order_id = order["orderId"]
                    order_type = order["type"]
                    
                    # ❌ Chỉ hủy các lệnh GRID (LIMIT, STOP_LIMIT) - Giữ lại TP/SL
                    if order_type in ["LIMIT", "STOP_LIMIT"]:
                        logging.warning(f"⚠️ Hủy lệnh GRID: {order['side']} @ {order['price']} (Loại: {order_type})")
                        action_futures.cancel_order_orderId(symbol, order_id)

                time.sleep(3)  # Chờ lệnh được hủy hoàn toàn
                open_orders = action_futures.get_open_order_count()
 
            

          
            # 🔥 Bước 6: Giám sát lệnh treo
            logging.info("\n🔥 Bước 6: Giám sát lệnh treo\n")
            
            current_time = int(time.time() * 1000)  # Timestamp hiện tại (ms)
            for order in open_orders_list:
                order_time = order.get("updateTime")  # Chỉ dùng updateTime, không fallback sang time

                if order_time is None:
                    logging.warning(f"⚠️ Lệnh {order['orderId']} không có updateTime, bỏ qua!")
                    continue  # Không hủy lệnh này để tránh nhầm lẫn

                order_age = (current_time - order_time) / 1000  # Chuyển ms → giây

                if order_age > botConfig.MAX_ORDER_WAIT_TIME:
                    logging.warning(f"⚠️ Lệnh {order['orderId']} đã treo {order_age:.2f}s, hủy lệnh!")
                    action_futures.cancel_order_orderId(order["symbol"], order["orderId"])  # Hủy lệnh
                    
            # 🔥 Bước 7: Đặt lệnh GRID TRADING nếu chưa đủ lệnh
          
            # Tích hợp Funding Rate
            funding_rate = update_price.get_funding_rate(symbol)
            if funding_rate is not None:
                logging.info(f"📊 Funding Rate hiện tại: {funding_rate:.6f}")
                if abs(funding_rate) > 0.001:  # Funding Rate > 0.1%
                    grid_levels = max(grid_levels // 2, botConfig.MIN_GRID_LEVELS)
                    logging.info(f"📊 Funding Rate cao ({funding_rate:.6f}), giảm lưới xuống {grid_levels}")          
            total_grid_orders = grid_levels * 2
            
            print(f"📊 Tổng số lệnh GRID: {total_grid_orders}")
            if open_orders < total_grid_orders:
                logging.info(f"📊 GRID TRADING → Đặt thêm lệnh cho {symbol} (hiện có {open_orders}/{total_grid_orders} lệnh)")

                missing_orders = total_grid_orders - open_orders
                missing_orders = min(missing_orders, botConfig.MAX_CONCURRENT_TRADES - open_orders)  # Giới hạn số lệnh

                # ✅ Đảm bảo luôn có giá trị mặc định
                existing_buy_orders = set()
                existing_sell_orders = set()
                # 🚀 Lấy danh sách lệnh mở
                open_orders_list = action_futures.get_pending_orders(symbol)
                if open_orders_list:
                    existing_buy_orders = {order["price"] for order in open_orders_list if order["side"] == "BUY"}
                    existing_sell_orders = {order["price"] for order in open_orders_list if order["side"] == "SELL"}

                if open_orders == 0:
                    for i in range(grid_levels):
                        # limit_buy_price = futures_price * (1 - (i + 1) * grid_spacing)
                        # limit_sell_price = futures_price * (1 + (i + 1) * grid_spacing)

                        if trend_direction == "UP":
                            limit_buy_price = (futures_price - grid_spacing * (i + 1)) * 1.002  # Tăng giá một chút
                            limit_sell_price = (futures_price + grid_spacing * (i + 1)) * 0.998  # Giảm giá một chút
                        elif trend_direction == "DOWN":
                            limit_buy_price = (futures_price - grid_spacing * (i + 1)) * 0.998  # Giảm giá một chút
                            limit_sell_price = (futures_price + grid_spacing * (i + 1)) * 1.002  # Tăng giá một chút
                        else:
                            limit_buy_price = futures_price * (1 - (i + 1) * grid_spacing)
                            limit_sell_price = futures_price * (1 + (i + 1) * grid_spacing)


                        if limit_buy_price not in existing_buy_orders:
                            action_futures.place_limit_long_with_stop_loss(
                                symbol, limit_buy_price, (order_value * leverage) / limit_buy_price
                            )

                        if limit_sell_price not in existing_sell_orders:
                            action_futures.place_limit_short_with_stop_loss(
                                symbol, limit_sell_price, (order_value * leverage) / limit_sell_price
                            )

                else:
                    latest_filled_price = market_prices["futures"].get("futures_price")
             

                    for i in range((missing_orders + 1) // 2):
                        # limit_buy_price = latest_filled_price * (1 - (i + 1) * grid_spacing)
                        # limit_sell_price = latest_filled_price * (1 + (i + 1) * grid_spacing)
                        if trend_direction == "UP":
                            limit_buy_price = latest_filled_price * (1 - (i + 1) * grid_spacing) * 1.002  # Tăng giá BUY một chút
                            limit_sell_price = latest_filled_price * (1 + (i + 1) * grid_spacing) * 0.998  # Giảm giá SELL một chút
                        elif trend_direction == "DOWN":
                            limit_buy_price = latest_filled_price * (1 - (i + 1) * grid_spacing) * 0.998  # Giảm giá BUY một chút
                            limit_sell_price = latest_filled_price * (1 + (i + 1) * grid_spacing) * 1.002  # Tăng giá SELL một chút
                        else:
                            limit_buy_price = latest_filled_price * (1 - (i + 1) * grid_spacing)
                            limit_sell_price = latest_filled_price * (1 + (i + 1) * grid_spacing)


                        if abs(limit_buy_price - limit_sell_price) < grid_spacing * 0.5:
                            logging.warning("⚠️ Khoảng cách lệnh quá nhỏ, điều chỉnh lại!")
                            continue

                        if limit_buy_price not in existing_buy_orders:
                            action_futures.place_limit_long_with_stop_loss(
                                symbol, limit_buy_price, (order_value * leverage) / limit_buy_price
                            )

                        if limit_sell_price not in existing_sell_orders:
                            action_futures.place_limit_short_with_stop_loss(
                                symbol, limit_sell_price, (order_value * leverage) / limit_sell_price
                            )

                time.sleep(1)  # Đợi API cập nhật danh sách lệnh
                open_orders_list = action_futures.get_pending_orders(symbol)  # Cập nhật danh sách lệnh mở
 
        except Exception as e:
            logging.error(f"❌ Lỗi trong quá trình chạy bot: {e}")

        logging.info("\n⏳ Đợi trước khi chạy vòng tiếp theo...\n")
       
        time.sleep(botConfig.CHECK_ORDER_INTERVAL)
        sync_times.sync_time()

# 🔥 Hàm phụ trợ: Tính trung bình giá vào lệnh của vị thế
def calculate_position_center(active_positions):
    if not active_positions:
        return None
    total_position_size = sum(abs(float(pos["positionAmt"])) for pos in active_positions)
    if total_position_size == 0:
        return None
    weighted_entry_price = sum(float(pos["entryPrice"]) * abs(float(pos["positionAmt"])) for pos in active_positions)
    return weighted_entry_price / total_position_size
# 🔥 Xác định tâm lưới cải tiến
def determine_grid_center(futures_price, active_positions, open_orders_list, order_book, atr_data, trend_direction):
    """
    Xác định tâm lưới dựa trên xu hướng thị trường (UP, DOWN, NEUTRAL).
    """
    # 1️⃣ Xác định giá trung bình có trọng số của vị thế mở
    position_center = calculate_position_center(active_positions) or futures_price

    # 2️⃣ Trung bình giá từ lệnh treo (nếu có)
    order_center = futures_price  # Mặc định là giá hiện tại nếu không có lệnh treo
    if open_orders_list:
        buy_orders = [float(order["price"]) for order in open_orders_list if order["side"] == "BUY"]
        sell_orders = [float(order["price"]) for order in open_orders_list if order["side"] == "SELL"]
        if buy_orders and sell_orders:
            order_center = (min(buy_orders) + max(sell_orders)) / 2


    # 3️⃣ Trung bình giá từ Order Book (nếu có)
    book_center = futures_price  # Mặc định là giá hiện tại nếu không có dữ liệu
    if order_book and "bids" in order_book and "asks" in order_book:
        try:
            best_bid = float(order_book["bids"][0][0])
            best_ask = float(order_book["asks"][0][0])
            book_center = (best_bid + best_ask) / 2
        except (IndexError, KeyError, ValueError):
            logging.warning("⚠️ Lỗi khi lấy dữ liệu Order Book, dùng giá Futures thay thế!")

    # 4️⃣ Tính trung bình có trọng số từ các nguồn giá
    candidates = [
        (position_center, 0.4),
        (order_center, 0.3),
        (book_center, 0.2),
        (futures_price, 0.1)
    ]
    valid_candidates = [(value, weight) for value, weight in candidates if value is not None]

    total_weight = sum(weight for _, weight in valid_candidates)
    if total_weight == 0:
        grid_center_price = futures_price
    else:
        grid_center_price = sum(value * weight for value, weight in valid_candidates) / total_weight

    # 5️⃣ **Điều chỉnh lưới theo xu hướng thị trường**
    grid_adjustment = 0
    if trend_direction == "UP":
        grid_adjustment = grid_center_price * 0.005  # Dịch lưới lên 0.5%
        logging.info("📊 Xu hướng TĂNG, dịch lưới lên 0.5%")
    elif trend_direction == "DOWN":
        grid_adjustment = -grid_center_price * 0.005  # Dịch lưới xuống 0.5%
        logging.info("📊 Xu hướng GIẢM, dịch lưới xuống 0.5%")
    else:
        logging.info("📊 Xu hướng trung lập, giữ nguyên lưới.")

    # 🔥 **Áp dụng điều chỉnh lưới**
    grid_center_price += grid_adjustment

    logging.info(f"📊 Tâm lưới mới sau điều chỉnh: {grid_center_price:.8f}")
    return grid_center_price



def main_start():
    logging.info("🚀 KHỞI ĐỘNG CẢ HAI LUỒNG...\n")
    monitor_thread = threading.Thread(target=monitor_positions, daemon=True)
    main_thread = threading.Thread(target=main_loop, daemon=True)
    monitor_thread.start()
    main_thread.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("⏹ Dừng bot...")

if __name__ == "__main__":
    main_start()
     

