
# def monitor_positions():
#     """ Luồng riêng kiểm tra TP/SL và đóng vị thế khi cần. """
#     while True:
#         try:
#             logging.info("\n🔄 [Monitor] Kiểm tra vị thế mở để đóng nếu đạt TP/SL hoặc FORCE_TAKE_PROFIT...\n")
#             action_futures.summary_profit()
#             active_positions = action_futures.get_active_trades()
           
#             if not active_positions:
#                 time.sleep(botConfig.CHECK_PROFIT_INTERVAL)
#                 continue

#             # logging.info("\n🔄 Kiểm tra vị thế mở để đóng nếu đạt TP/SL hoặc FORCE_TAKE_PROFIT...\n")     
#             atr_data = strategyChoose.tech_data_furtures()
#             atr_value = atr_data[-1]["atr"] if atr_data else None
            
#             for pos in active_positions:
#                 symbol = pos["symbol"]
#                 entry_price = float(pos["entryPrice"])
#                 position_size = float(pos["positionAmt"])
#                 current_price = float(pos["markPrice"])
#                 unrealized_profit = float(pos["unRealizedProfit"])  # Lợi nhuận chưa thực hiện

#                 # Tính toán Take Profit (TP) và Stop Loss (SL)
#                 take_profit_price = entry_price + (atr_value * 2)
#                 stop_loss_price = entry_price - (atr_value * max(botConfig.ATR_MULTIPLIER, 2 if atr_value < botConfig.MIN_ATR else 1.5))

#                 # Tính phần trăm lời/lỗ so với vốn ban đầu
#                 profit_percent = (current_price - entry_price) / entry_price * 100 if position_size > 0 else (entry_price - current_price) / entry_price * 100

#                 logging.info(f"📊 Vị thế {symbol} | Entry: {entry_price:.2f} | Current: {current_price:.2f} | PnL: {unrealized_profit:.2f} USDT ({profit_percent:.2f}%)")

#                 # 🚀 Kiểm tra FORCE_TAKE_PROFIT (Đóng ngay khi lợi nhuận >= mức cài đặt)
#                 if unrealized_profit >= botConfig.FORCE_TAKE_PROFIT:
#                     if position_size > 0:
#                         close_order = action_futures.close_long_position(symbol)
#                         if close_order:
#                             logger.log_trade_closure(symbol, "LONG", entry_price, current_price, "FORCE_TAKE_PROFIT", unrealized_profit, profit_percent)
#                             logging.info(f"✅ Đóng LONG {symbol} vì đạt FORCE_TAKE_PROFIT: {unrealized_profit:.2f} USDT")
#                     elif position_size < 0:
#                         close_order = action_futures.close_short_position(symbol)
#                         if close_order:
#                             logger.log_trade_closure(symbol, "SHORT", entry_price, current_price, "FORCE_TAKE_PROFIT", unrealized_profit, profit_percent)
#                             logging.info(f"✅ Đóng SHORT {symbol} vì đạt FORCE_TAKE_PROFIT: {unrealized_profit:.2f} USDT")

#                 # 🚀 Nếu đạt Take Profit (TP) → Đóng vị thế
#                 elif position_size > 0 and current_price >= take_profit_price:
#                     close_order = action_futures.close_long_position(symbol)
#                     if close_order:
#                         logger.log_trade_closure(symbol, "LONG", entry_price, current_price, "TAKE_PROFIT", unrealized_profit, profit_percent)
#                         logging.info(f"✅ Đóng LONG {symbol} tại {current_price:.2f} USDT | TP đạt {take_profit_price:.2f} USDT")

#                 elif position_size < 0 and current_price <= take_profit_price:
#                     close_order = action_futures.close_short_position(symbol)
#                     if close_order:
#                         logger.log_trade_closure(symbol, "SHORT", entry_price, current_price, "TAKE_PROFIT", unrealized_profit, profit_percent)
#                         logging.info(f"✅ Đóng SHORT {symbol} tại {current_price:.2f} USDT | TP đạt {take_profit_price:.2f} USDT")

#                 # ❌ Nếu chạm Stop Loss (SL) → Đóng vị thế
#                 elif position_size > 0 and current_price <= stop_loss_price:
#                     close_order = action_futures.close_long_position(symbol)
#                     if close_order:
#                         logger.log_trade_closure(symbol, "LONG", entry_price, current_price, "STOP_LOSS", unrealized_profit, profit_percent)
#                         logging.warning(f"❌ Cắt lỗ LONG {symbol} tại {current_price:.2f} USDT | SL đạt {stop_loss_price:.2f} USDT")

#                 elif position_size < 0 and current_price >= stop_loss_price:
#                     close_order = action_futures.close_short_position(symbol)
#                     if close_order:
#                         logger.log_trade_closure(symbol, "SHORT", entry_price, current_price, "STOP_LOSS", unrealized_profit, profit_percent)
#                         logging.warning(f"❌ Cắt lỗ SHORT {symbol} tại {current_price:.2f} USDT | SL đạt {stop_loss_price:.2f} USDT")

#         except Exception as e:
#             logging.error(f"❌ Lỗi trong quá trình kiểm tra TP/SL: {e}")

#         time.sleep(botConfig.CHECK_PROFIT_INTERVAL)  # Đợi trước khi kiểm tra lại