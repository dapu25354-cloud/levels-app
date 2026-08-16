"""
統一實(9907) 空手觀察(以第二證券商為準) 關卡監控
------------------------------------------------------------
背景:核心持股在第一證券商,不列入這裡管理；第二證券商(這套系統追蹤的帳戶)目前沒有這檔。
教訓:統一實是「慢牛、量小」的牛皮股 -> 硬加碼容易買在小波動高點,想加要等『帶量真轉強』。

關卡(均線即時算):
  帶量站上季高+RSI轉強 = 才考慮小量接回(訊號明確才動,別憑感覺加)
  20MA上多頭           = 沒你的事,觀察就好
  跌破20MA/60MA        = 慢牛偏弱,繼續空手
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "9907.TW"
NAME = "統一實"

# ====== 你的部位(app 內持倉管理可改;第二證券商戶目前空手) ======
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
    vol5 = float(df['Volume'].iloc[-6:-1].mean())
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    vr = vol / vol5 if vol5 else 0
    return price, ma20, ma60, high60, rs14, vr

TOL = 0.01
def judge(price, ma20, ma60, high60, rs14, vr):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    # 真轉強:帶量貼季高+RSI強 = 才考慮加回(明確訊號才動)
    if rs14 >= 65 and price >= high60 * 0.99 and vr >= 1.3:
        return (f"🟢 {price:.2f} 帶量轉強(RSI {rs14:.0f}、量比{vr:.1f}、貼季高{high60:.2f}) — "
                f"這才是可以考慮加回的訊號(小量、別追);沒這組訊號別憑感覺加。")
    # 明顯跌破季線:繼續空手就好,不用特別留意
    if price < ma60 * 0.97 or (price < ma60 * (1 - TOL) and vr >= 1.5):
        return (f"⚪ {price:.2f} 明顯跌破季線({ma60:.2f}) — 空手,繼續觀察就好。")
    # 牛皮帶/均線下小幅晃:這種股常態,空手不用理
    if price < ma20 * (1 - TOL):
        return (f"⚪ {price:.2f} 牛皮偏弱(在均線下小幅晃、量比{vr:.1f}縮) — 空手,沒你的事,不用接。")
    return (f"⚪ {price:.2f} 慢牛盤整、沒事(月線 {ma20:.2f}上) — 空手觀察,牛皮量小、沒訊號別手癢接。")

def run():
    price, ma20, ma60, high60, rs14, vr = get_data()
    print(f"=== {NAME}({SYMBOL}) 空手觀察(以第二證券商為準) ===")
    if SHARES:
        pnl = (price / COST - 1) * 100
        print(f"市價：{price:.2f}    成本：{COST}（帳面 {pnl:+.1f}%）    {SHARES} 股")
    else:
        print(f"市價：{price:.2f}    空手(核心持股在第一券商,不列入這裡)")
    print(f"月線：{ma20:.2f}    季線：{ma60:.2f}    季高：{high60:.2f}    RSI：{rs14:.0f}    量比：{vr:.1f}")
    print(judge(price, ma20, ma60, high60, rs14, vr))
    print(f"\n備忘：空手,帶量貼季高+RSI轉強才考慮小量接回 / 沒訊號別憑感覺加 / 別因不甘心手癢接")

if __name__ == "__main__":
    run()
