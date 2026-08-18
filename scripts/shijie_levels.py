"""
世界先進(5347) 核心+機動 高賣低撿 關卡監控
------------------------------------------------------------
背景:老手長期持股,一直保有部位、來回做過好幾次。核心不動,機動倉「高了賣、回檔撿」。
     世界是健康多頭、創新高、RSI不過熱 -> 可能續創高,機動沒撿到不可惜,別追高。
節奏:創高/高檔賣機動鎖利;先看季線判斷中期方向,再用月線與成交量確認;核心永遠不動。
股數:見 app 內持倉管理(不寫死於程式碼,曾多次高賣低撿調整)。

關卡(均線即時算):
  創高/高檔  = 賣機動倉鎖利(核心不動)
  20MA上中間 = 先抱著觀察,不追高
  站在60MA上拉回20MA = 確認止跌後再考慮小加
  跌破20MA但仍守60MA = 觀察量價,不急著撿
  低於60MA   = 中期轉弱,空手不宜積極追買
  月線附近   = 月線保衛戰,搭配量價確認是否止跌
  放量跌破月線 = 轉弱加劇,機動停止加碼/評估換股
  站回60MA   = 中期轉強,可再提高部位
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
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.7 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01
NEAR_MONTH = 0.03

def judge(price, ma20, ma60, high60, vol, vol_ma20):
    vdesc, ratio = vol_desc(vol, vol_ma20)
    near_month = abs(price - ma20) / ma20 <= NEAR_MONTH

    if price >= high60 * 0.99:
        vnote = "有量撐，賣得放心" if ratio >= 1.2 else "量沒特別放大，賣一部分就好、別急著全出"
        return (f"🔴 {price} 創高/高檔({high60:.0f})，{vnote} — 賣機動倉鎖利。核心不動。")

    if price >= ma60:
        return (f"🟢 中期轉強｜站回季線 {ma60:.0f} — 可再提高部位；"
                f"月線 {ma20:.0f} 附近仍先確認止跌再小加。")

    if price < ma20 * (1 - TOL) and ratio >= 1.5:
        return (f"⚠️ 月線失守｜放量轉弱 — 現價 {price:.0f}，月線 {ma20:.0f}；"
                f"轉弱加劇，機動部位停止加碼／評估換股。站回季線 {ma60:.0f} 再重評。")

    if near_month and price < ma60:
        return (f"🟠 中期轉弱｜月線保衛戰\n"
                f"現價 {price:.0f}，月線 {ma20:.0f}，季線 {ma60:.0f}；{vdesc}。\n"
                f"趨勢：低於季線，中期轉弱，空手不宜積極追買。\n"
                f"量縮守 {ma20:.0f}：續抱觀察，確認止跌後再考慮小加。\n"
                f"放量跌破 {ma20:.0f}：轉弱加劇，機動部位停止加碼／評估換股。\n"
                f"站回 {ma60:.0f}：中期轉強，可再提高部位。")

    if price < ma60:
        return (f"🟡 中期轉弱｜先觀察 — 現價 {price:.0f} 低於季線 {ma60:.0f}；"
                f"{vdesc}，量縮下跌不能直接判定大戶逃跑，空手不宜積極追買。")

    return (f"⚪ 中間區 — 現價 {price:.0f}、月線 {ma20:.0f}、季線 {ma60:.0f}；"
            f"先看量價確認止跌，有機動就抱著觀察。")

def run():
    price, ma20, ma60, high60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}先進({SYMBOL}) 核心+機動 高賣低撿 ===")
    print(f"市價：{price}    月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    持股 {SHARES}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, vol, vol_ma20))
    print(f"\n備忘：創高賣機動 / 低於季線先看中期轉弱 / 月線附近看能否守住 / 量縮守住才等止跌小加 / 放量跌破月線停止加碼、評估換股 / 站回季線再提高部位 / 核心永遠不動")

if __name__ == "__main__":
    run()
