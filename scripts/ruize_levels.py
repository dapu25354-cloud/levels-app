"""
銳澤(7703) 醒了才碰 監控 —— 空手版
------------------------------------------------------------
背景:銳澤是全帳最弱的「悶股」——公司不爛(去年EPS 8.72、海外布局),
     但股票一整年在 181~241 悶著不動,別人季漲40~70%、它才+6.8%。
     沒有實際持股,純觀察名單,等它證明自己醒了才考慮碰。

⚠️ 跟汎銓不一樣:這是「弱股」,不是「強股回檔」。
   所以【不是等接回低接】——買弱股的便宜=攤平弱股=你的老毛病。
   只有它「證明自己醒了」(帶量突破套牢區)才值得回頭碰,否則錢放強股。

關卡(白話):
  醒了才碰 = 帶量站上 215(清掉近期套牢頭部)。沒帶量突破前,它再便宜都別買。
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "7703.TWO"
NAME = "銳澤"

# ====== 計畫(可改) ======
WAKE = 215         # 帶量站上這裡=開始有醒的跡象(清掉近期213套牢頭部)
VOL_X = 1.5        # 悶股要醒,量要更明顯:今天量 ÷ 前5日均量 ≥ 1.5
RED_BODY = 0.03    # 大紅K:收盤比開盤高 3% 以上
# ============================


def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="3mo", auto_adjust=False)
    if df.empty:
        tk = yf.Ticker("7703.TW")
        df = tk.history(period="3mo", auto_adjust=False)
    o = float(df['Open'].iloc[-1])
    c = float(df['Close'].iloc[-1])
    prev = float(df['Close'].iloc[-2])
    vol = float(df['Volume'].iloc[-1])
    vol5 = float(df['Volume'].iloc[-6:-1].mean())
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            c = float(rp)
    except Exception:
        pass
    chg = (c / prev - 1) * 100
    body = (c - o) / o if o else 0
    vr = vol / vol5 if vol5 else 0
    return c, chg, body, vr


def judge(price, chg, body, vr):
    big_vol = vr >= VOL_X
    big_red = body >= RED_BODY and chg > 0

    # 帶量突破套牢頭部 = 開始有醒的跡象
    if price >= WAKE and big_vol and big_red:
        return (f"🟩 {price:.0f} —— 【有醒的跡象】帶量站上 {WAKE}(量比{vr:.1f}、紅K{body*100:.1f}%)。"
                f"但它是你換掉的弱股,要碰只接『證明轉強』的它:先小量試、別大買、別把強股的錢搬回來。")

    # 站上 215 但量沒跟上 = 悶股假突破最多
    if price >= WAKE:
        return (f"🟢 {price:.0f} —— 站到 {WAKE} 附近,但量沒跟上(量比{vr:.1f})。悶股假突破多,"
                f"沒帶量別當真、別追。等『帶量大紅K』再說。")

    # 還在悶 = 別買它的便宜
    return (f"⚪ {price:.0f} —— 還在悶(沒過 {WAKE})。這是你汰弱換強換掉的弱股,"
            f"【別買它的便宜】,錢放會動的強股。沒帶量突破 {WAKE} 之前,它再低都別碰。")


def run():
    price, chg, body, vr = get_data()
    print(f"=== {NAME}({SYMBOL}) 醒了才碰(空手) ===")
    print(f"市價：{price:.0f}（今天 {chg:+.1f}%）   量比：{vr:.1f}   醒的關卡：帶量站上 {WAKE}")
    print(judge(price, chg, body, vr))
    print("\n備忘：銳澤是悶股、不是強股回檔 / 只有帶量突破215才碰 / "
          "別低接弱股(=攤平老毛病) / 沒醒就把錢放強股")


if __name__ == "__main__":
    run()
