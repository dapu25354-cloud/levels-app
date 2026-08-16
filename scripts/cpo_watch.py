"""
CPO / 矽光子 觀察雷達 (尚未持有,等拉回有機會再上手)
------------------------------------------------------------
2026是CPO量產收割年、輝達押注矽光子=台股新主流。這些是高基期高波動飆股 -> 別追高,
等「拉回、不過熱」才小量試單。本工具幫你盯強弱與進場時機。

註:源傑科技是聯鈞(3450)子公司、無單獨乾淨代號,曝險用聯鈞代替。
   日月光投控價格波動大,實際以券商App為準。
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

WATCH = [
    # 聯鈞(3450)2026/06/26已試單轉持有 → 移到 lianjun_levels.py 盯,不在觀察區了
    ("4979.TWO", "華星光",   "AI資料中心高階光模組,800G放量、1.6T接棒"),
    ("3363.TWO", "上詮",     "光纖封裝,受惠台積電嘉義廠"),
    ("3711.TW",  "日月光投控","CPO先進封裝OSAT龍頭(大型、相對穩)"),
]

def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))

def analyze(code):
    tk = yf.Ticker(code)
    df = tk.history(period="4mo", auto_adjust=False)
    if df.empty:
        alt = code.replace(".TWO", ".TW") if ".TWO" in code else code.replace(".TW", ".TWO")
        df = yf.Ticker(alt).history(period="4mo", auto_adjust=False)
    if df.empty or len(df) < 60:
        return None
    c = df['Close']
    price = float(c.iloc[-1])
    prev = float(c.iloc[-2])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    high60 = float(c.iloc[-60:].max())
    rs14 = float(rsi(c).iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
        pc = info.get('regularMarketPreviousClose') or info.get('previousClose')
        if pc:
            prev = float(pc)
    except Exception:
        pass
    chg = (price / prev - 1) * 100 if prev else 0.0
    return price, ma20, ma60, high60, rs14, chg

def day_tag(chg):
    """今日漲跌一眼看到,大漲大跌先標出來,別被落後的均線判斷蓋掉。"""
    if chg >= 5:
        return f"🔺今日噴出 {chg:+.1f}%"
    if chg <= -5:
        return f"🔻今日急殺 {chg:+.1f}%"
    return f"今日 {chg:+.1f}%"

def signal(price, ma20, ma60, high60, rs14, chg):
    above20 = (price / ma20 - 1) * 100
    from_high = (price / high60 - 1) * 100
    if price < ma60:
        base = f"⚠️ 均線仍走弱(60日線 {ma60:.0f}下) — 結構未轉強,別追。"
        if chg >= 5:
            base += f" 但今天噴 {chg:+.1f}%,是跌深反彈第一根,看明天守不守得住、量有沒有續,別第一根就追。"
        return base
    if rs14 >= 75 or above20 >= 25:
        return f"🔴 過熱(RSI {rs14:.0f}、乖離 +{above20:.0f}%) — 等拉回,別追高。"
    if price <= ma20 * 1.06 and rs14 < 70:
        return f"🟢 拉回觀察區(近20日線 {ma20:.0f}、不過熱) — 有機會,可小量試單、設停損。"
    return f"⚪ 強但不極端(距季高 {from_high:+.0f}%) — 續觀察,等更好的拉回點。"

def run():
    print("=== 🔭 CPO/矽光子 觀察雷達 (尚未持有) ===")
    for code, name, role in WATCH:
        try:
            a = analyze(code)
            if not a:
                print(f"  {name}({code}) 抓取失敗")
                continue
            price, ma20, ma60, high60, rs14, chg = a
            print(f"\n  {name}({code})  市價 {price:.1f}  ({day_tag(chg)})  20MA {ma20:.0f}  60MA {ma60:.0f}  RSI {rs14:.0f}")
            print(f"    {role}")
            print(f"    {signal(price, ma20, ma60, high60, rs14, chg)}")
        except Exception as e:
            print(f"  {name}({code}) 出錯: {e}")
    print("\n要上手前跟我說,我幫該檔做完整功課(基本面/法人/進場點)再決定。源傑曝險用聯鈞。")

if __name__ == "__main__":
    run()
