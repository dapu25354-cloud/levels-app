"""
寶成(9904) 等接回 監控 —— 空手版（之前弱、已汰弱出清）
------------------------------------------------------------
背景:這檔之前空頭、弱,你依建議「汰弱出清」(正確紀律,不是被洗)。現在你「空手」。
     近況:近3月緩跌-12%(28.9→25.4),但近一個月在 25-26 橫盤『不再破底』,
     且量越來越大(13000→23000張)= 低檔有人在接、換手。
     底背離成立:5/04 價25.6/RSI7(恐慌殺到底) → 5/28 價25.2/RSI36(同低價、賣壓大減)。
     → 像在打底、有資金吸籌,但「還沒確認」。基本面是製鞋代工龍頭,不是地雷,所以值得等。

你的上車訊號(白話):
  訊號1「開始盯」 = 還在 25-26 箱型內。意思是【打底中,先別買、看著】。
  訊號2「上車」   = 『帶量站上 26、收盤站穩』(量比放大 + 收上26)。
                   意思是【換手成功、由空轉多,可以小量試接】。
  破底警示       = 帶量摜破 25 = 打底失敗,別接、繼續空手。

紀律:底背離只是「跌不太動了」,不是買進訊號。沒看到訊號2(帶量站上26)之前,
     紅一下綠一下都不要追。別因為「以前有過、現在跌深」就手癢接falling刀。
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "9904.TW"
NAME = "寶成"

# ====== 你的計畫(可改) ======
BREAKOUT = 26      # 帶量站上這裡站穩 = 換手成功(訊號2,可小量試接)
BOX_LOW = 25       # 箱型下緣;帶量摜破 = 打底失敗、別接
VOL_X = 1.3        # 「帶量」門檻:今天量 ÷ 前5日均量 ≥ 1.3
# ============================


def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))


def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="3mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    prev = float(c.iloc[-2])
    vol = float(df['Volume'].iloc[-1])
    vol5 = float(df['Volume'].iloc[-6:-1].mean())   # 前5日均量(不含今天)
    rs14 = float(rsi(c).iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    chg = (price / prev - 1) * 100
    vr = vol / vol5 if vol5 else 0
    return price, chg, vr, rs14


def judge(price, chg, vr, rs14):
    big_vol = vr >= VOL_X

    # 帶量站上26 = 換手成功
    if price >= BREAKOUT and big_vol:
        return (f"🟩 {price:.1f} —— 【上車訊號2:可以接了】帶量站上 {BREAKOUT}"
                f"(量比{vr:.1f})= 換手成功、由空轉多。可【小量試接】(別一次全押),"
                f"接回後守 {BOX_LOW}(帶量跌破再走)。")

    # 站上26但沒量 = 還沒確認
    if price >= BREAKOUT:
        return (f"🟡 {price:.1f} —— 站上 {BREAKOUT} 了但『沒量』(量比{vr:.1f})。"
                f"假突破風險,等帶量站穩再說、先別追。")

    # 摜破25 = 打底失敗
    if price < BOX_LOW:
        return (f"⚠️ {price:.1f} —— 跌破箱型下緣 {BOX_LOW}{'、且帶量' if big_vol else ''}。"
                f"打底失敗、空頭續走,別接、繼續空手等。")

    # 在 25-26 箱型內打底
    return (f"🟢 {price:.1f}（RSI{rs14:.0f}）—— 【訊號1:打底中,先別買】"
            f"還在 {BOX_LOW}-{BREAKOUT} 箱型,今天量比{vr:.1f}、{chg:+.1f}%。"
            f"底背離+量增=有人在接,但還沒帶量突破 {BREAKOUT}。看著、別手癢接刀。")


def run():
    price, chg, vr, rs14 = get_data()
    print(f"=== {NAME}({SYMBOL}) 等接回(空手) ===")
    print(f"市價：{price:.1f}（今天 {chg:+.1f}%）   量比：{vr:.1f}   RSI：{rs14:.0f}   "
          f"上車線：站上{BREAKOUT}帶量   守：{BOX_LOW}")
    print(judge(price, chg, vr, rs14))
    print("\n備忘：訊號1=25-26箱型『打底中先別買』 / "
          "訊號2=帶量站上26『換手成功可小量試接』 / 帶量破25=打底失敗別接。沒突破不追。")


if __name__ == "__main__":
    run()
