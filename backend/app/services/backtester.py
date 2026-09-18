import uuid
from typing import Dict, Any, List
from fastapi import HTTPException
from app.schemas.backtest import BacktestRequest, BacktestResponse, BacktestTrade, EquityPoint
from app.schemas.risk import RiskRequest
from app.services.indicators import indicator_service
from app.services.strategy import strategy_service
from app.services.risk_manager import risk_manager_service

class BacktestEngine:
    def run(self, req: BacktestRequest) -> BacktestResponse:
        if req.initial_capital <= 0:
            raise HTTPException(status_code=400, detail="Initial capital must be positive.")
        if req.risk_percentage <= 0:
            raise HTTPException(status_code=400, detail="Risk percentage must be positive.")

        # 1. Fetch Indicators (which contains historical OHLCV data as well)
        history = indicator_service.get_indicators(req.symbol)
        if not history or len(history) == 0:
            raise HTTPException(status_code=404, detail=f"No historical data found for {req.symbol}.")

        # 2. State tracking
        current_capital = req.initial_capital
        equity_curve: List[EquityPoint] = []
        trades: List[BacktestTrade] = []
        
        # Drawdown tracking
        peak_equity = current_capital
        max_drawdown = 0.0

        # Position State
        position = None  # None or Dict containing position details

        # 3. Chronological Iteration
        for i in range(len(history)):
            candle = history[i]
            timestamp = candle['timestamp']
            
            # Record Equity at open of candle (or start of day) before processing intraday High/Lows
            # If we have an open position, equity fluctuates. We'll value it at Open for simplicity of daily record.
            current_equity = current_capital
            if position:
                unrealized = 0
                if position['side'] == 'LONG':
                    unrealized = (candle['open'] - position['entry_price']) * position['quantity']
                elif position['side'] == 'SHORT':
                    unrealized = (position['entry_price'] - candle['open']) * position['quantity']
                current_equity += unrealized
                
            equity_curve.append(EquityPoint(timestamp=timestamp, equity=current_equity))
            
            # Update peak equity and max drawdown
            if current_equity > peak_equity:
                peak_equity = current_equity
            drawdown = (peak_equity - current_equity) / peak_equity * 100 if peak_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            # Intra-trade execution checks if position is open
            if position:
                # Check Stop Loss & Target breaches
                high = candle['high']
                low = candle['low']
                
                exit_triggered = False
                exit_reason = ""
                exit_price = 0.0

                if position['side'] == 'LONG':
                    hit_sl = low <= position['stop_loss']
                    hit_target = high >= position['target']
                    
                    if hit_sl and hit_target:
                        # Conservative assumption: SL hit first
                        exit_triggered = True
                        exit_reason = "STOP_LOSS"
                        exit_price = position['stop_loss']
                    elif hit_sl:
                        exit_triggered = True
                        exit_reason = "STOP_LOSS"
                        exit_price = position['stop_loss']
                    elif hit_target:
                        exit_triggered = True
                        exit_reason = "TARGET"
                        exit_price = position['target']
                        
                elif position['side'] == 'SHORT':
                    hit_sl = high >= position['stop_loss']
                    hit_target = low <= position['target']
                    
                    if hit_sl and hit_target:
                        # Conservative assumption: SL hit first
                        exit_triggered = True
                        exit_reason = "STOP_LOSS"
                        exit_price = position['stop_loss']
                    elif hit_sl:
                        exit_triggered = True
                        exit_reason = "STOP_LOSS"
                        exit_price = position['stop_loss']
                    elif hit_target:
                        exit_triggered = True
                        exit_reason = "TARGET"
                        exit_price = position['target']

                if exit_triggered:
                    # Calculate P&L
                    gross_pnl = 0
                    if position['side'] == 'LONG':
                        gross_pnl = (exit_price - position['entry_price']) * position['quantity']
                    else:
                        gross_pnl = (position['entry_price'] - exit_price) * position['quantity']
                        
                    current_capital += gross_pnl
                    
                    ret_pct = (gross_pnl / (position['entry_price'] * position['quantity'])) * 100 if position['quantity'] > 0 else 0

                    trades.append(BacktestTrade(
                        trade_id=f"BT-{uuid.uuid4().hex[:6].upper()}",
                        symbol=req.symbol,
                        side=position['side'],
                        quantity=position['quantity'],
                        entry_timestamp=position['entry_timestamp'],
                        entry_price=position['entry_price'],
                        exit_timestamp=timestamp,
                        exit_price=exit_price,
                        stop_loss=position['stop_loss'],
                        target=position['target'],
                        exit_reason=exit_reason,
                        gross_pnl=round(gross_pnl, 2),
                        net_pnl=round(gross_pnl, 2),
                        return_percentage=round(ret_pct, 2),
                        strategy_reason=position['strategy_reason']
                    ))
                    position = None
                    continue # Skip signal generation if we just exited, evaluating next candle for new entries

            # If no open position, evaluate strategy
            if not position and i < len(history) - 1:
                # We generate signal using candle[i] (closing data).
                # We will execute at candle[i+1] open.
                
                strategy_res = strategy_service.evaluate(req.symbol, indicator_data=candle)
                
                if strategy_res and strategy_res['signal'] in ['BUY', 'SELL']:
                    # Signal generated! Execute at next candle's open
                    next_candle = history[i+1]
                    entry_price = next_candle['open']
                    
                    side = "LONG" if strategy_res['signal'] == 'BUY' else "SHORT"
                    
                    # Calculate Stop Loss and Target
                    if side == "LONG":
                        sl_price = entry_price * (1 - (req.stop_loss_percentage / 100))
                        tg_price = entry_price * (1 + (req.target_percentage / 100))
                    else:
                        sl_price = entry_price * (1 + (req.stop_loss_percentage / 100))
                        tg_price = entry_price * (1 - (req.target_percentage / 100))

                    # 4. Risk Validation using the existing risk manager
                    risk_req = RiskRequest(
                        capital=current_capital,
                        risk_percentage=req.risk_percentage,
                        entry_price=entry_price,
                        stop_loss=sl_price,
                        target=tg_price,
                        direction=side
                    )
                    
                    try:
                        risk_res = risk_manager_service.calculate(risk_req)
                        if risk_res.position_size > 0:
                            # Enter position
                            strat_conditions = strategy_res.get('conditions', {})
                            reason_str = f"Conditions: SMA: {strat_conditions.get('sma')}, RSI: {strat_conditions.get('rsi')}, MACD: {strat_conditions.get('macd')}"
                            
                            position = {
                                "side": side,
                                "quantity": risk_res.position_size,
                                "entry_price": entry_price,
                                "entry_timestamp": next_candle['timestamp'],
                                "stop_loss": sl_price,
                                "target": tg_price,
                                "strategy_reason": reason_str
                            }
                    except Exception as e:
                        # Risk manager rejected (e.g., SL=Entry)
                        pass

        # End of backtest: Close any open position at the last available close price
        if position:
            last_candle = history[-1]
            exit_price = last_candle['close']
            exit_reason = "END_OF_BACKTEST"
            
            gross_pnl = 0
            if position['side'] == 'LONG':
                gross_pnl = (exit_price - position['entry_price']) * position['quantity']
            else:
                gross_pnl = (position['entry_price'] - exit_price) * position['quantity']
                
            current_capital += gross_pnl
            ret_pct = (gross_pnl / (position['entry_price'] * position['quantity'])) * 100 if position['quantity'] > 0 else 0

            trades.append(BacktestTrade(
                trade_id=f"BT-{uuid.uuid4().hex[:6].upper()}",
                symbol=req.symbol,
                side=position['side'],
                quantity=position['quantity'],
                entry_timestamp=position['entry_timestamp'],
                entry_price=position['entry_price'],
                exit_timestamp=last_candle['timestamp'],
                exit_price=exit_price,
                stop_loss=position['stop_loss'],
                target=position['target'],
                exit_reason=exit_reason,
                gross_pnl=round(gross_pnl, 2),
                net_pnl=round(gross_pnl, 2),
                return_percentage=round(ret_pct, 2),
                strategy_reason=position['strategy_reason']
            ))
            
            # Ensure final equity reflects the close
            equity_curve[-1].equity = current_capital

        # Calculate Metrics
        total_pnl = current_capital - req.initial_capital
        return_pct = (total_pnl / req.initial_capital) * 100
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.gross_pnl > 0])
        losing_trades = len([t for t in trades if t.gross_pnl <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        gross_profits = sum([t.gross_pnl for t in trades if t.gross_pnl > 0])
        gross_losses = sum([abs(t.gross_pnl) for t in trades if t.gross_pnl < 0])
        profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (999.0 if gross_profits > 0 else 0.0)

        return BacktestResponse(
            symbol=req.symbol,
            initial_capital=req.initial_capital,
            final_equity=round(current_capital, 2),
            total_pnl=round(total_pnl, 2),
            return_percentage=round(return_pct, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_drawdown, 2),
            trades=trades,
            equity_curve=equity_curve
        )

backtest_engine = BacktestEngine()
