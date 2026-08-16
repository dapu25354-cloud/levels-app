"""
長榮航(2618) 已出清 -> 空手等接回 觀察
------------------------------------------------------------
背景:逃生門成功出清過(等於原封不動拿回本金、結束躺一年的死錢)。
     去年看線型買進、想來回做,結果它一路盤跌、把使用者套住,放到「忘了它存在」=死錢、沒題材。
定位:現在空手。這檔是『盤跌趨勢股』不是箱型 -> 別因為「曾經套過、不甘心」就急著接回、別來回做。
     接回的唯一條件:它真的轉強(站上季線+量出來+題材),不是跌一點就想撿。沒到=放著看,不動手。
成本/股數/上次出清價:見 app 內持倉管理(不寫死於程式碼)。

關卡(均線即時算):
  站上60MA且RSI回升 = 🟢真轉強才考慮小量接回(別追、回測不破再進)
  60MA下/盤跌中     = ⚪沒你的事,空手看戲、別手癢接falling刀
  又貼季高過熱      = 🔴若哪天又彈到高點,提醒:這是逃生門股,別再進場套自己
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2618.TW"
NAME = "長榮航"

# ====== 你的部位(app 內持倉管理可改) ======
COST, SHARES = positions_store.get_lot(SYMBOL)
_lot = positions_store.get_lot_full(SYMBOL)
LAST_EXIT = _lot.get("last_exit")  # 出清價,當作接回參考:回得遠又真轉強才考慮
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
    # 空手等接回:只在「真轉強」才點頭,其餘一律按住手
    if rs14 >= 72 and price >= high60 * 0.98:
        return (f"🔴 {price} 又過熱貼高(RSI {rs14:.0f}、近季高 {high60:.1f}) — 提醒:這是逃生門股,"
                f"你已賺到出場,別再進場套自己。")
    if price >= ma60 and rs14 >= 50:
        return (f"🟢 {price} 站上季線({ma60:.1f})、RSI {rs14:.0f}回升 — 唯一可考慮接回的情況。"
                f"但要小量、回測不破再進,別追;沒題材就還是別貪。")
    if price < ma60:
        return (f"⚪ {price} 在季線({ma60:.1f})下/盤跌中 — 沒你的事,空手看戲。"
                f"別因為「曾經套過、不甘心」就手癢接falling刀,它是盤跌趨勢股,別來回做。")
    return (f"⚪ {price} 雖在季線({ma60:.1f})之上但 RSI ({rs14:.0f}) 仍偏弱/無動能 — 空手看戲，別急著接回。")

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 已出清 → 空手等接回 ===")
    if LAST_EXIT:
        print(f"市價：{price}    （已於 {LAST_EXIT} 出清,逃生門成功、本金落袋）")
    else:
        print(f"市價：{price}    空手")
    print(f"月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, rs14))
    print(f"\n備忘：空手 / 真轉強(站季線+量+題材)才小量接 / 別來回做(盤跌趨勢股) / 不甘心≠進場理由")

if __name__ == "__main__":
    run()
