"""
順達(3211) 順勢持有/賣強 關卡監控
------------------------------------------------------------
背景:健康多頭、貼近季高但「沒過熱」(RSI中性)。沒有賣訊號時別在沒訊號時手癢砍掉正在好好賺的股。
策略:健康就順勢抱;真過熱(RSI高+貼高)才賣強鎖利;跌破均線才保護獲利。
成本/股數:見 app 內持倉管理(不寫死於程式碼,曾多次校正/加碼/減碼)。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 賣強鎖利(這才是賣點)
  創高             = 帶量突破續抱別賣飛,沒過熱別急賣
  20MA上未過熱     = 健康多頭,順勢抱,沒訊號別手癢賣
  跌破20MA         = 回檔,留意守60日線、別追
  跌破60MA         = 轉弱,保護獲利減碼
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "3211.TWO"
NAME = "順達"

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
    if df.empty:
        df = yf.Ticker("3211.TW").history(period="4mo", auto_adjust=False)
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
def judge(price, ma20, ma60, high60, rs14, vol, vol_ma20):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < ma60 * (1 - TOL):
        return (f"⚠️ {price} 跌破季線({ma60:.0f}) — 轉弱,保護獲利減碼。")
    if price < ma20 * (1 - TOL):
        return (f"🟡 {price} 跌破月線({ma20:.0f}) — 回檔,留意守季線({ma60:.0f})、別追。")
    if rs14 >= 70 and price >= high60 * 0.98:
        return (f"🔴 {price} 過熱貼高(RSI {rs14:.0f}、近季高 {high60:.0f}) — 這才是賣強鎖利的點。")
    if price >= high60 * 0.99:
        ratio = vol / vol_ma20 if vol_ma20 else 1.0
        vnote = "有量撐，帶量突破可信" if ratio >= 1.2 else "但量沒放大，先別當真突破"
        return (f"🟢 {price} 創高({high60:.0f})，{vnote} — 沒過熱別急賣、別賣飛。")
    return (f"⚪ {price} 健康多頭(月線 {ma20:.0f}上、RSI {rs14:.0f}不熱) — 順勢抱,"
            f"沒訊號別手癢賣。要賣等它「過熱貼高」或「跌破月線」。")

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 順勢持有/賣強 ===")
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price}    成本：{COST}（帳面 {pnl:+.1f}%）    {SHARES} 股")
    else:
        print(f"市價：{price}    空手")
    print(f"月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, rs14, vol, vol_ma20))
    print(f"\n備忘：RSI≥70貼高才賣強 / 月線上健康抱、別手癢 / 跌破月線留意 / 跌破季線減碼")

if __name__ == "__main__":
    run()
