"""
中鋼(2002) 牛皮悶股/汰弱換強盯著 關卡監控
------------------------------------------------------------
背景:傳產牛皮股,波動小、動能低(季僅+1.6%),貼著均線牛皮整理。
     註:中鋼曾因FTSE台灣指數季度調整出現爆量被動買盤(非看多),別把指數調整的量當突破。
策略:它就是低波動悶股,放著、別期待大漲、別花心力;弱就換股。同銳澤邏輯但更牛皮。

關卡(均線即時算):
  帶量突破季高 = 難得醒來(且要排除指數調整假量)才當真
  均線上牛皮   = 低波動悶著,放著、別加碼,換股候選
  跌破20MA     = 走弱,留意60日線
  跌破60MA站不回 = 轉弱,汰弱換強
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2002.TW"
NAME = "中鋼"

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
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
        return f"⚠️ {price} 跌破季線({ma60:.1f})站不回 — 牛皮股都破線=轉弱,汰弱換強。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.1f}) — 走弱,留意季線({ma60:.1f})。"
    if price >= high60 * 0.99:
        ratio = vol / vol_ma20 if vol_ma20 else 1.0
        if ratio >= 1.5:
            vnote = f"量有放大(均量{ratio:.1f}倍)，比較像真的醒了"
        else:
            vnote = f"但量沒放大(只有均量{ratio:.1f}倍)，小心是指數調整的假量，先別當真"
        return f"🟢 {price} 逼近/突破季高({high60:.1f})，{vnote}。"
    return (f"⚪ {price} 牛皮悶股(月線 {ma20:.1f}上、低波動) — 放著、別期待大漲、別花心力,換股候選。")

def run():
    price, ma20, ma60, high60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 牛皮悶股/汰弱換強盯著 ===")
    print(f"市價：{price}    月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, vol, vol_ma20))
    print(f"\n備忘：低波動別期待大漲 / 突破季高要看有沒有放量、排除指數調整假量 / 跌破季線汰弱換強")

if __name__ == "__main__":
    run()
