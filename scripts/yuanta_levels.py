"""
元大金(2885) 核心+機動 高賣低撿 關卡監控
------------------------------------------------------------
部位:核心(買約十年的古老長線)=永遠不動;機動倉可操作,高賣低撿賺價差。
背景:健康多頭、貼近季高。核心吃長線,機動「貼高賣、拉回撿」賺價差。
     ※這檔是「箱型來回做」OK的標的;別把這套用在會噴的趨勢股(緯穎/順達)。
策略:核心永遠不動;機動高賣低撿;分清「回檔(正常)」與「轉弱(連核心都留意)」。
成本/股數(核心/機動兩組):見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  貼近季高/強勢  = 賣機動倉鎖利(核心不動)
  20MA上中間     = 多頭健康,機動抱/核心不動,等貼高賣或回20MA撿
  拉回20MA附近   = 撿回機動倉的點
  跌破20MA       = 回檔,守60日線別慌、機動別追
  跌破60MA站不回 = 轉弱,連核心都留意(罕見)
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2885.TW"
NAME = "元大金"
CORE_COST, CORE_SHARES = positions_store.get_lot(SYMBOL, "core")
TACTICAL_COST, TACTICAL_SHARES = positions_store.get_lot(SYMBOL, "tactical")

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high60 = float(c.iloc[-60:].max())  # 約當季高
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
def judge(price, ma20, ma60, high60, vol=None, vol_ma20=None):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < ma60 * (1 - TOL):
        return (f"⚠️ {price} 跌破季線({ma60:.1f})站不回 — 轉弱,連核心都該留意(罕見)。")
    if price < ma20 * (1 - TOL):
        return (f"🟡 {price} 跌破月線({ma20:.1f}) — 回檔,守季線({ma60:.1f})別慌、機動別追。")
    if price <= ma20 * 1.03:
        return (f"🟢 {price} 拉回月線({ma20:.1f})附近 — 撿回機動倉的點(核心本就不動)。")
    if price >= high60 * 0.985:
        return (f"🔴 {price} 貼近季高({high60:.1f})強勢 — 賣機動倉鎖利,核心不動。別等翻黑才砍。")
    return (f"⚪ {price} 多頭健康(月線 {ma20:.1f}上) — 機動抱、核心不動;等貼高賣機動 或 回 {ma20:.1f} 撿回。")

def run():
    price, ma20, ma60, high60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 核心+機動 高賣低撿 ===")
    print(f"市價：{price}    月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}")
    print(f"成交量：{vdesc}")
    parts = []
    if CORE_SHARES:
        core_pnl = (price / CORE_COST - 1) * 100
        parts.append(f"核心{CORE_SHARES:.0f}股(成本{CORE_COST}、帳面 {core_pnl:+.0f}%)不動")
    if TACTICAL_SHARES:
        tac_pnl = (price / TACTICAL_COST - 1) * 100
        parts.append(f"機動{TACTICAL_SHARES:.0f}股(成本{TACTICAL_COST}、帳面 {tac_pnl:+.0f}%)可操作")
    print("部位：" + (" + ".join(parts) if parts else "空手"))
    print(judge(price, ma20, ma60, high60))
    print(f"\n備忘：貼高賣機動 / 回月線撿回機動 / 核心永遠不動 / 跌破季線連核心都留意")

if __name__ == "__main__":
    run()
