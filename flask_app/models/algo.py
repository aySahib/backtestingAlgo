import yfinance as yf
import pandas as pd
from datetime import timedelta
import socket

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State

# Constants
TZ = "America/Los_Angeles"

# --- Data Download -------------------------------------------------------
def get_data(symbol: str, start: str, end: str,
             interval: str, auto_adjust: bool=True) -> pd.DataFrame:
    dl_kwargs = {"interval": interval, "auto_adjust": auto_adjust, "progress": False}
    def _chunk(s, e):
        k = dl_kwargs.copy()
        k.update({"start": s.strftime('%Y-%m-%d'), "end": e.strftime('%Y-%m-%d')})
        return yf.download(symbol, **k)

    start_dt = pd.to_datetime(start)
    end_dt   = pd.to_datetime(end)
    if 'm' in interval and (end_dt - start_dt) > timedelta(days=7):
        parts, cur = [], start_dt
        while cur < end_dt:
            nxt = min(cur + timedelta(days=7), end_dt)
            parts.append((cur, nxt))
            cur = nxt
        df = pd.concat(_chunk(s,e) for s,e in parts).drop_duplicates()
    else:
        df = _chunk(start_dt, end_dt)

    df = df.tz_convert(TZ)
    if df.columns.nlevels > 1:
        df.columns = df.columns.droplevel(1)
    df = df[['Open','High','Low','Close','Volume']]
    if df.empty:
        raise RuntimeError(f"No data for {symbol} {start}→{end}")
    return df

# --- Broker & Backtest Engine -------------------------------------------
class Broker:
    def __init__(self, cash=100_000):
        self.initial_cash = cash
        self.cash, self.position = cash, 0
        self.trades, self.equity_curve = [], []

    def buy(self, ts, price, size=1):
        self.cash  -= price*size
        self.position += size
        self.trades.append({"timestamp":ts,"side":"BUY","price":price,"size":size})

    def sell(self, ts, price, size=1):
        self.cash  += price*size
        self.position -= size
        self.trades.append({"timestamp":ts,"side":"SELL","price":price,"size":size})

    def record_equity(self, ts, price):
        self.equity_curve.append({
            "timestamp": ts,
            "equity": self.cash + self.position*price
        })

class Strategy:
    def on_start(self, data, broker): pass
    def on_bar(self, timestamp, bar, broker): pass


def run_backtest(symbol, start, end, interval, strategy_cls, cash):
    data   = get_data(symbol, start, end, interval)
    broker = Broker(cash)
    strat  = strategy_cls()
    strat.symbol = symbol
    strat.on_start(data, broker)

    for ts, bar in data.iterrows():
        strat.on_bar(ts, bar, broker)
        broker.record_equity(ts, bar['Close'])

    eq     = pd.DataFrame(broker.equity_curve).set_index('timestamp')
    eq.index = pd.to_datetime(eq.index)
    eq.rename(columns={'equity':'Equity'}, inplace=True)
    trades = pd.DataFrame(broker.trades)
    return eq, trades, broker.initial_cash, data

# --- Performance Analysis -----------------------------------------------
def analyze_performance(trades_df, equity_df, initial_cash):
    start_bal = initial_cash
    end_bal   = equity_df['Equity'].iloc[-1]
    net_pl    = end_bal - start_bal

    t = trades_df.copy(); t['pnl'] = 0.0
    buys = []
    for i, r in t.iterrows():
        if r.side == 'BUY':
            buys.append(r.price)
        elif r.side == 'SELL' and buys:
            entry = buys.pop(0)
            t.at[i, 'pnl'] = r.price - entry

    wins  = (t['pnl'] > 0).sum()
    total = (t['pnl'] != 0).sum()
    winr  = wins/total*100 if total>0 else 0

    return {
        'start_balance': start_bal,
        'end_balance':   end_bal,
        'net_pl':        net_pl,
        'total_trades':  total,
        'wins':          wins,
        'win_rate':      winr
    }

# --- Utility ------------------------------------------------------------
def find_free_port():
    s = socket.socket(); s.bind(('',0))
    p = s.getsockname()[1]; s.close(); return p

# --- Fair Value Gap (FVG) Utilities ------------------------------------
def add_fvg_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['high_lag2'] = df['High'].shift(2)
    df['low_lag2']  = df['Low'].shift(2)
    df['fvg_bull']  = df['high_lag2'] < df['Low']
    df['fvg_bear']  = df['low_lag2'] > df['High']
    return df


def mark_fvg_on_figure(fig: dict, df: pd.DataFrame) -> dict:
    sweeps = add_fvg_flags(df)
    for idx, row in sweeps.iterrows():
        if row['fvg_bull']:
            bottom, top = row['high_lag2'], row['Low']
            fig['layout'].setdefault('shapes', []).append({
                'type':'rect','xref':'x','yref':'y',
                'x0':df.index[df.index.get_loc(idx)-2],'x1':idx,
                'y0':bottom,'y1':top,
                'fillcolor':'rgba(0,255,0,0.2)','line':{'width':0}
            })
        if row['fvg_bear']:
            top, bottom = row['low_lag2'], row['High']
            fig['layout'].setdefault('shapes', []).append({
                'type':'rect','xref':'x','yref':'y',
                'x0':df.index[df.index.get_loc(idx)-2],'x1':idx,
                'y0':bottom,'y1':top,
                'fillcolor':'rgba(255,0,0,0.2)','line':{'width':0}
            })
    return fig

# --- Swing Point Utilities ----------------------------------------------
def add_swing_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['swing_low']  = (df['Low'] < df['Low'].shift(1))  & (df['Low'] < df['Low'].shift(-1))
    df['swing_high'] = (df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))
    return df


def mark_swings_on_figure(fig: dict, df: pd.DataFrame) -> dict:
    swings = add_swing_flags(df)
    lows   = swings[swings['swing_low']]
    highs  = swings[swings['swing_high']]
    fig['data'].append({
        'x': lows.index, 'y': lows['Low'], 'mode':'markers','name':'Swing Lows', 'marker':{'symbol':'triangle-down','size':10,'color':'lime'}
    })
    fig['data'].append({
        'x': highs.index,'y': highs['High'],'mode':'markers','name':'Swing Highs','marker':{'symbol':'triangle-up','size':10,'color':'magenta'}
    })
    return fig

# --- Dash App -------------------------------------------------------------
app = dash.Dash(__name__, title="Futures Backtest Dashboard")
server = app.server
# CSS Start 
app.layout = html.Div(
    style={'backgroundColor':'#111','color':'#EEE','fontFamily':'Arial'},
    children=[
        html.H1("Futures Backtest Dashboard", style={'textAlign':'center','marginBottom':'1rem'}),
        html.Div(
            style={'display':'flex','gap':'1rem','justifyContent':'center','flexWrap':'wrap','marginBottom':'1rem'},
            children=[
                html.Div([html.Label("Symbol",style={'color':'#EEE'}),dcc.Input(id='symbol',type='text',value='ES=F',style={'backgroundColor':'#222','color':'#EEE','width':'6rem'})]),
                html.Div([html.Label("Start",style={'color':'#EEE'}),dcc.DatePickerSingle(id='start',date='2025-04-01',display_format='YYYY-MM-DD')]),
                html.Div([html.Label("End",style={'color':'#EEE'}),dcc.DatePickerSingle(id='end',date='2025-04-18',display_format='YYYY-MM-DD')]),
                html.Div([html.Label("Interval",style={'color':'#EEE'}),dcc.Dropdown(id='interval',options=[{'label':i,'value':i}for i in['1m','5m','15m','30m','1h','4h','1d']],value='5m')]),
                html.Div([html.Label("Cash",style={'color':'#EEE'}),dcc.Input(id='cash',type='number',value=50000,style={'width':'6rem'})]),
                html.Div([html.Label("Show Swings",style={'color':'#EEE'}),dcc.Checklist(id='show-swings',options=[{'label':'Swing Highs/Lows','value':'show_swings'}],value=[],style={'color':'#EEE'})]),
                html.Div([html.Label("Show FVGs",style={'color':'#EEE'}),dcc.Checklist(id='show-fvgs',options=[{'label':'Fair Value Gaps','value':'show_fvgs'}],value=[],style={'color':'#EEE'})]),
                html.Button("Run Backtest",id='run-btn',n_clicks=0)
            ]
        ),
        html.Div(id='metrics',style={'display':'flex','justifyContent':'space-around','backgroundColor':'#222','padding':'0.5rem','borderRadius':'4px','marginBottom':'1rem'}),
        dcc.Tabs(id='tabs', children=[
            dcc.Tab(label='Equity Curve', children=[dcc.Graph(id='equity-graph')]),
            dcc.Tab(label='Price & Volume', children=[dcc.Graph(id='price-graph')]),
            dcc.Tab(label='Trades Table', children=[
                dash_table.DataTable(
                    id='trades-table',
                    columns=[
                        {'name':'Timestamp','id':'timestamp'},
                        {'name':'Side','id':'side'},
                        {'name':'Price','id':'price'},
                        {'name':'Size','id':'size'},
                        {'name':'P&L','id':'pnl'}
                    ],
                    data=[],
                    page_size=20,
                    style_header={'backgroundColor':'#333','color':'#EEE'},
                    style_cell={'backgroundColor':'#222','color':'#EEE'},
                    style_table={'backgroundColor':'#111'}
                )
            ])
        ])
    ]
)

@app.callback(
    Output('metrics','children'), Output('equity-graph','figure'), Output('price-graph','figure'), Output('trades-table','data'),
    Input('run-btn','n_clicks'), State('symbol','value'), State('start','date'), State('end','date'),
    State('interval','value'), State('cash','value'), State('show-swings','value'), State('show-fvgs','value')
)
def update(n, sym, st, en, intrv, cash, show_swings, show_fvgs):
    if not n:
        return dash.no_update
    eq, trades, init_cash, data = run_backtest(sym, st, en, intrv, MyStrategy, cash)
    perf = analyze_performance(trades, eq, init_cash)
    cards = [html.Div([html.H4(lbl), html.P(val)]) for lbl, val in [
        ("Start", perf['start_balance']),
        ("End", perf['end_balance']),
        ("Net P/L", perf['net_pl']),
        ("# Trades", perf['total_trades']),
        ("Win%", f"{perf['win_rate']:.1f}%")
    ]]
    eq_fig = {
        'data': [{'x': eq.index, 'y': eq['Equity'], 'type': 'line'}],
        'layout': {
            'paper_bgcolor': '#111', 'plot_bgcolor': '#111', 'font': {'color': '#EEE'}, 'title': 'Equity Curve',
            'xaxis': {'type': 'date', 'tickformat': '%I:%M %p'}, 'timezone': 'America/Los_Angeles'
        }
    }
    price_fig = {
        'data': [{'x': data.index, 'open': data['Open'], 'high': data['High'], 'low': data['Low'], 'close': data['Close'], 'type': 'candlestick'}],
        'layout': {
            'paper_bgcolor': '#111', 'plot_bgcolor': '#111', 'font': {'color': '#EEE'}, 'title': 'Price Chart',
            'xaxis': {'type': 'date', 'tickformat': '%I:%M %p'}, 'timezone': 'America/Los_Angeles'
        }
    }
    if 'show_swings' in show_swings:
        price_fig = mark_swings_on_figure(price_fig, data)
    if 'show_fvgs' in show_fvgs:
        price_fig = mark_fvg_on_figure(price_fig, data)
    table = trades.assign(pnl=lambda df: df['size'] * (df['price'].diff().fillna(0))).to_dict('records')
    return cards, eq_fig, price_fig, table
# CSS End
# --- Strategy Definition (at bottom) ------------------------------------
class MyStrategy(Strategy):
    def on_start(self, data, broker):
        self.data5 = data
        self.swp_high = None
        self.swp_low = None
        self.phase = 'init'
        start, end = data.index[0].strftime('%Y-%m-%d'), data.index[-1].strftime('%Y-%m-%d')
        self.data1 = get_data(self.symbol, start, end, '1m')
        self.last_fvg = add_fvg_flags(self.data1)

    def on_bar(self, ts, bar, broker):
        # At 06:30 AM, capture the most recent 5m swing
        if ts.hour == 6 and ts.minute == 30:
            swings = add_swing_flags(self.data5)
            swings_before = swings[swings.index < ts]
            if not swings_before.empty:
                self.swp_high = swings_before[swings_before['swing_high']]['High'].iloc[-1]
                self.swp_low  = swings_before[swings_before['swing_low']]['Low'].iloc[-1]
                self.phase = 'wait_sweep'
            return

        # Wait for liquidity sweep
        if self.phase == 'wait_sweep':
            if bar['High'] > self.swp_high:
                self.direction = 'sell'
                self.phase = 'enter_fvg'
            elif bar['Low'] < self.swp_low:
                self.direction = 'buy'
                self.phase = 'enter_fvg'
            return

        # Enter on FVG close on 1m
        if self.phase == 'enter_fvg':
            fvg = self.last_fvg[self.last_fvg['fvg_bear' if self.direction=='buy' else 'fvg_bull']]
            if not fvg.empty:
                idx = fvg.index[-1]
                zone_high = fvg.loc[idx, 'Low'] if self.direction=='buy' else fvg.loc[idx, 'high_lag2']
                zone_low  = fvg.loc[idx, 'high_lag2'] if self.direction=='buy' else fvg.loc[idx, 'Low']
                recent1 = self.data1.loc[:ts].iloc[-1]
                if self.direction=='buy' and recent1['Close'] > zone_high:
                    entry, sl = recent1['Close'], self.swp_low
                    tp = entry + (entry - sl)
                    broker.buy(ts, entry, 1)
                    broker.sell(ts, tp, 1)
                    self.phase='done'
                elif self.direction=='sell' and recent1['Close'] < zone_low:
                    entry, sl = recent1['Close'], self.swp_high
                    tp = entry - (sl - entry)
                    broker.sell(ts, entry, 1)
                    broker.buy(ts, tp, 1)
                    self.phase='done'
            return

if __name__ == "__main__":
    port = find_free_port()
    print(f"http://127.0.0.1:{port}")
    app.run(debug=True, host='127.0.0.1', port=port, use_reloader=False)
   