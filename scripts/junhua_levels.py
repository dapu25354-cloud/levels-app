"""
均華(6640) 撿貨/加碼紀律 關卡監控
------------------------------------------------------------
背景:強基本面股大修正(季高→低點大跌;營收/毛利數據亮眼,能見度佳)。
     曾套牢後停損一半控風險,重新在支撐區接回,持續撿貨中。
重點:這是「強股支撐區撿貨」非恐慌攤平。但還沒確認止跌 -> 要有「停止加碼線」、別無限攤、留子彈。
成本/股數:見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  跌破前低(SUPPORT) = 停止加碼、重新評估(修正比想的深)
  SUPPORT~20日線    = 撿貨區但還沒止跌,小量分批可以、守前低,手要留
  站回20日線        = 止跌確認,較放心的加碼點
  收復60日線        = 趨勢修好回多頭,核心順勢抱
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "6640.TWO"
NAME = "均華"

# ====== 你的部位(app 內持倉管理可改) ======
COST, SHARES = positions_store.get_lot(SYMBOL)
SUPPORT = 1006   # 前低,跌破=停止加碼線(股票的技術價位,不是個人成本)
# ============================================

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    if df.empty:
        df = yf.Ticker("6640.TW").history(period="4mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, vol, vol_ma20

def vol_desc(vol, vol_ma20):
    """把成交量翻成白話：放量/量縮/量平，配上跟均量的比例。"""
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01
def judge(price, ma20, ma60, vol=None, vol_ma20=None):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < SUPPORT:
        return (f"⛔ {price} 跌破前低 {SUPPORT} — 好公司被爛行情拖(基本面沒壞、是族群被殺估值)。"
                f"抱住持股、停止加碼、別往下攤(老毛病!);站回 月線({ma20:.0f})才算止跌再動作。")
    if price < ma20 * (1 - TOL):
        return (f"🟡 {price} 撿貨區但還沒止跌(月線 {ma20:.0f} 下) — 小量分批可以,"
                f"守 {SUPPORT}、手要留別梭。站回 {ma20:.0f} 才算止跌。")
    if price < ma60 * (1 - TOL):
        return (f"🟢 {price} 站回月線({ma20:.0f}),止跌確認 — 較放心的加碼點;看能否收復季線({ma60:.0f})。")
    return (f"⚪ {price} 收復季線({ma60:.0f}),趨勢修好回多頭 — 核心順勢抱。")

def run():
    price, ma20, ma60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 撿貨/加碼紀律 ===")
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price}    均價：{COST}（帳面 {pnl:+.1f}%）    {SHARES} 股    "
              f"月線：{ma20:.0f}    季線：{ma60:.0f}")
    else:
        print(f"市價：{price}    空手    月線：{ma20:.0f}    季線：{ma60:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60))
    print(f"\n備忘：跌破{SUPPORT}=停手、別往下攤(老毛病) / 沒站回月線前什麼都別做 / "
          f"基本面好是「抱著等」不是「汰弱」 / 站回月線才算止跌")

if __name__ == "__main__":
    run()
