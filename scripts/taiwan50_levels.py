"""
元大台灣50(0050) 大盤核心ETF/養著回檔撿 關卡監控
------------------------------------------------------------
背景:追蹤台灣前50大,台積電權重約一半 -> 等於「半個台積電 ETF」,大盤縮影。
     這波殺AI/半導體,它首當其衝跟著晃;但它是分散一籃子,不會像單一弱股要汰弱。
策略:這是「定期養、回檔分批撿」的工具,不是恐慌盤殺進殺出的。別追高、別恐慌殺。
     看月線(20MA)當第一道防線;真破才往季線靠近時分批接。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 別追高,等回檔再撿
  20MA上未過熱   = 健康,定期養著,回檔分批撿
  跌破20MA       = 回檔加深,別殺,往季線靠近分批接
  跌破60MA       = 大盤轉弱,放慢加碼、抱住別恐慌(ETF不汰弱)
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "0050.TW"
NAME = "元大台灣50"

# ====== 你的部位(app 內持倉管理可改) ======
COST, SHARES = positions_store.get_lot(SYMBOL)
# ============================================

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
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, high60, rs14, vol, vol_ma20

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01
def judge(price, ma20, ma60, high60, rs14, vol=None, vol_ma20=None):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price} 跌破季線({ma60:.1f}) — 大盤轉弱,放慢加碼、抱住別恐慌(ETF不汰弱)。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.1f}) — 回檔加深,別殺,往季線({ma60:.1f})靠近分批接。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 過熱貼高(RSI {rs14:.0f}) — 別追高,等回檔再撿。"
    return (f"⚪ {price} 健康(月線 {ma20:.1f}上、RSI {rs14:.0f}) — 定期養著,回檔分批撿、別追高。")

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 大盤核心ETF/養著回檔撿 ===")
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price}    成本：{COST}（帳面 {pnl:+.1f}%）    {SHARES} 股")
    else:
        print(f"市價：{price}    空手")
    print(f"月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, rs14))
    print(f"\n備忘：半個台積電ETF / 定期養回檔撿、別恐慌殺 / 月線第一防線 / 跌破季線抱住別汰弱")

if __name__ == "__main__":
    run()
