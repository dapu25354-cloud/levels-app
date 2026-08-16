"""
統一超(2912) 定存領息試單 關卡監控 —— 持有版
------------------------------------------------------------
背景:定存/領息試單。曾過熱貼高(RSI高、即將除權息)賣強鎖利全數出清過一次,
     試單目的達成,乾淨執行「過熱就賣強」的紀律,不是停損、是賺了收手。
     除權息後拉回,重新小量試單。
策略:定存領息股,平常抱著不追不減;真的過熱貼高才賣強鎖利(同上次的紀律),
     不是漲一點就急著獲利了結,也不因為「定存股」就無腦硬抱到轉弱都不理。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  跌破季線         = 趨勢轉弱,先觀察,別攤平
  月線~季高之間     = 合理範圍,續抱不追不減
  過熱貼高(近季高+RSI高) = 賣強鎖利(部分),別等回頭
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2912.TW"
NAME = "統一超"
COST, SHARES = positions_store.get_lot(SYMBOL)


def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))


def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high60 = float(c.iloc[-60:].max())
    rs14 = float(rsi(c).iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, high60, rs14


TOL = 0.01
def judge(price, ma20, ma60, high60, rs14):
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price:.1f} 跌破季線({ma60:.1f}) — 趨勢轉弱,先觀察,別攤平,定存股沒有硬抱到底的理由。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price:.1f} 過熱貼高(RSI {rs14:.0f}、近季高{high60:.1f}) — 賣強鎖利,同上次的紀律,別等回頭。"
    return f"⚪ {price:.1f} 合理範圍(月線{ma20:.1f}~季高{high60:.1f}) — 續抱不追不減,領息心態。"


def run():
    price, ma20, ma60, high60, rs14 = get_data()
    print(f"=== {NAME}({SYMBOL}) 定存領息試單 ===")
    print(f"市價：{price:.1f}    均價：{COST}（帳面 {(price/COST-1)*100:+.1f}%）    持股 {SHARES}股" if SHARES else f"市價：{price:.1f}    空手")
    print(f"月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}    RSI：{rs14:.0f}")
    print(judge(price, ma20, ma60, high60, rs14))
    print("\n備忘：跌破季線先觀察別攤平 / 過熱貼高賣強鎖利 / 合理範圍就抱著領息不折騰")


if __name__ == "__main__":
    run()
