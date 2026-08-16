"""
大立光(3008) 過熱核心保護/拉回觀察 關卡監控
------------------------------------------------------------
背景:千金股、噴過頭(RSI高、大乖離)、貼季高。回起來會很急 -> 核心重「保護獲利」。
策略:多頭健康抱核心;過熱別追加;想接回等「拉回、乖離收斂」,別追高檔。同智伸科邏輯。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。另有一筆更低成本的核心持股在別的券商,不列入這裡管理。

關卡(均線即時算):
  過熱(RSI高/乖離大) = 賣強區,核心抱、別追加,接回再等
  20日線之上多頭     = 核心順勢抱
  跌破20日線         = 回檔(乖離大回得急),核心留意、守60日線
  跌破60日線站不回   = 波段轉弱,保護獲利、核心可減
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "3008.TW"
NAME = "大立光"
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
    return price, ma20, ma60, rs14, vol, vol_ma20

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01
def judge(price, ma20, ma60, rs14, vol=None, vol_ma20=None):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    above20 = (price / ma20 - 1) * 100
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price} 跌破季線({ma60:.0f})站不回 — 波段轉弱,保護獲利、核心可減。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.0f}) — 乖離大回得急,核心留意、守季線({ma60:.0f});別接。"
    if rs14 >= 75 or above20 >= 25:
        return (f"🔴 {price} 過熱(RSI {rs14:.0f}、乖離 +{above20:.0f}%) — 賣強區,核心抱著別追加;"
                f"想接回等拉回、乖離收斂,別追高檔。")
    return f"⚪ {price} 多頭健康(月線 {ma20:.0f}上) — 核心順勢抱,跌破月線再留意。"

def run():
    price, ma20, ma60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 過熱核心保護/拉回觀察 ===")
    if SHARES:
        print(f"市價：{price}    券商均價約：{COST}（帳面 {(price/COST-1)*100:+.0f}%）    約 {SHARES} 股")
    else:
        print(f"市價：{price}    空手")
    print(f"月線：{ma20:.0f}    季線：{ma60:.0f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, rs14))
    print(f"\n備忘：過熱賣強別追加 / 月線上抱核心 / 跌破月線留意 / 跌破季線保護獲利減")

if __name__ == "__main__":
    run()
