"""
世界先進(5347) 核心+機動 高賣低撿 關卡監控
------------------------------------------------------------
背景:老手長期持股,一直保有部位、來回做過好幾次。核心不動,機動倉「高了賣、回檔撿」。
     世界是健康多頭、創新高、RSI不過熱 -> 可能續創高,機動沒撿到不可惜,別追高。
節奏:創高/高檔賣機動鎖利;只有仍站在60日線上、拉回20日線才撿多一點;跌破60日線後機動停撿;核心永遠不動。
股數:見 app 內持倉管理(不寫死於程式碼,曾多次高賣低撿調整)。

關卡(均線即時算):
  創高/高檔  = 賣機動倉鎖利(核心不動)
  20MA上中間 = 小撿可以、大撿等回20MA;有機動就抱等更高
  站在60MA上拉回20MA = 撿多一點(主要回補點)
  跌破20MA但仍守60MA = 小量觀察,不大撿
  跌破60MA   = 趨勢轉弱,機動先停撿、核心留意
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "5347.TWO"
NAME = "世界"
_, SHARES = positions_store.get_lot(SYMBOL)  # 這檔不追蹤成本,只追蹤核心+機動總持股

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    if df.empty:
        df = yf.Ticker("5347.TW").history(period="4mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high60 = float(c.iloc[-60:].max())
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, high60, vol, vol_ma20

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01
def judge(price, ma20, ma60, high60, vol, vol_ma20):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < ma60 * (1 - TOL):
        return (f"⚠️ {price} 跌破季線({ma60:.0f}) — 趨勢轉弱,機動先停撿、核心留意。")
    if price < ma20 * (1 - TOL):
        return (f"🟡 {price} 跌破月線({ma20:.0f}) — 回檔加深,可分批撿、守季線({ma60:.0f})。")
    if price <= ma20 * 1.05:
        return (f"🟢 {price} 拉回月線({ma20:.0f})附近 — 撿多一點(機動倉)。核心不動。")
    if price >= high60 * 0.99:
        ratio = vol / vol_ma20 if vol_ma20 else 1.0
        vnote = "有量撐，賣得放心" if ratio >= 1.2 else "但量沒特別放大，賣一部分就好、別急著全出"
        return (f"🔴 {price} 創高/高檔({high60:.0f})，{vnote} — 賣機動倉鎖利。核心不動。")
    return (f"⚪ {price} 中間區(月線 {ma20:.0f}上、未到高 {high60:.0f}) — 小撿可以、"
            f"大撿等回 {ma20:.0f};有機動就抱等更高賣。")

def run():
    price, ma20, ma60, high60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}先進({SYMBOL}) 核心+機動 高賣低撿 ===")
    print(f"市價：{price}    月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    持股 {SHARES}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, vol, vol_ma20))
    print(f"\n備忘：創高賣機動 / 只有站在季線({ma60:.0f})上拉回月線({ma20:.0f})才撿 / 跌破季線就停撿 / 重新站回季線後再評估 / 核心永遠不動")

if __name__ == "__main__":
    run()
