"""
台新新光金(2887) 金融核心/持有賣強 關卡監控
------------------------------------------------------------
背景:台新金已與新光金合併,2887 現為「台新新光金」存續公司、大型金控。合併綜效題材,
     但合併後股本變大、籌碼要重新沉澱,別只看題材。金融這波漲多,當核心抱、沒空盯。
策略:沒過熱就抱;真過熱貼高(RSI≥70)才像元大金/中信金那樣賣強鎖利一部分;跌破均線才留意。

關卡(均線即時算):
  過熱貼高(RSI≥70+近季高) = 可賣強鎖利一部分(同元大金/中信金邏輯)
  20MA上未過熱   = 健康多頭,抱著,沒訊號別賣
  跌破20MA       = 回檔,守60日線別慌
  跌破60MA       = 轉弱,減碼
"""
import sys
from datetime import date
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2887.TW"
NAME = "台新新光金"

def get_catalyst_note():
    """噴出段時查『為什麼』:先看有沒有快到的除權息(yfinance calendar),抓得到就講具體日期,抓不到就叫她自己查新聞。"""
    try:
        cal = yf.Ticker(SYMBOL).calendar
        exdiv = cal.get('Ex-Dividend Date')
        if isinstance(exdiv, list):
            exdiv = exdiv[0] if exdiv else None
        if exdiv:
            days = (exdiv - date.today()).days
            if 0 <= days <= 30:
                return f"查到原因了:{exdiv.month}/{exdiv.day}要除權息(有現金+股票股利),這波多半是搶息行情。"
            if -5 <= days < 0:
                return f"查到原因了:{exdiv.month}/{exdiv.day}才剛除權息沒幾天,價格可能還在消化除息效應。"
    except Exception:
        pass
    return None

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
def judge(price, ma20, ma60, high60, rs14, vol=None, vol_ma20=None, catalyst=None):
    if abs(ma20 - ma60) / ma60 <= 0.015 and abs(price - ma60) / ma60 <= 0.015 and abs(price - ma20) / ma20 <= 0.02:
        return f"⚪ {price} 均線糾結({ma20:.0f}/{ma60:.0f})、牛皮盤整 — 沒選邊前抱著、別追進追出;帶量站回 {ma60*(1+TOL):.0f} 才算轉強、帶量破 {ma20*(1-TOL):.0f} 才算轉弱。"
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price} 跌破季線({ma60:.1f}) — 轉弱,減碼。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 跌破月線({ma20:.1f}) — 回檔,守季線({ma60:.1f})別慌。"
    aberration = (price - ma60) / ma60
    vol_ratio = (vol / vol_ma20) if (vol and vol_ma20) else 1.0
    if aberration >= 0.25 and vol_ratio >= 1.3 and price >= high60 * 0.98:
        reason = catalyst or "沒查到近期除權息,這波噴出應該是消息面/題材帶動,建議自己上網查一下最近新聞比較保險。"
        return (f"🚀 {price} 噴出段(貼季線{aberration*100:.0f}%、量是均量{vol_ratio*100:.0f}%) — "
                f"噴出段的樣子就是:短時間內離季線拉開一大截(健康多頭通常沒這麼誇張)+成交量放很大,"
                f"背後通常有題材或事件在推,不是正常漲法。{reason} "
                f"這種時候RSI過熱是鈍化的,會一直卡在高檔喊過熱、但價格照樣噴,別理它;"
                f"真正該盯的是「量縮下來」(買盤衝完了)或「跌破月線」(短均線都守不住),那才是噴出結束、該收手的訊號。")
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 過熱貼高(RSI {rs14:.0f}) — 可賣強鎖利一部分(同元大金/中信金邏輯)。"
    return (f"⚪ {price} 健康多頭(月線 {ma20:.1f}上、RSI {rs14:.0f}) — 抱著,沒過熱別賣。")

def run():
    price, ma20, ma60, high60, rs14, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 金融核心/持有賣強 ===")
    print(f"市價：{price}    月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}    RSI：{rs14:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60, rs14, vol, vol_ma20, get_catalyst_note()))
    print(f"\n備忘：合併後籌碼重新沉澱別只看題材 / RSI≥70貼高才賣強鎖利 / 月線上抱著 / 跌破季線減碼")

if __name__ == "__main__":
    run()
