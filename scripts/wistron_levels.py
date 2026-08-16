"""
緯創(3231) 箱型關卡監控
------------------------------------------------------------
盯 4 個價位，抓真實市價比對，直接給動作：
  144 = 60日線/最後防線(跌破=箱型破,停手)
  150~152 = 下緣買進區(分批接)
  188~194 = 上緣賣出區(分批減)
  194 = 突破區(帶量才算數,讓核心倉跑)
箱子中間(152~188)= 按兵不動。

註：緯創沒配股問題,但顯示價仍走 info['regularMarketPrice'] 抓真實市價(跟券商一致),
    成交量用來判斷突破真假(帶量突破才可信)。
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "3231.TW"
NAME = "緯創"

# 箱型關卡
FLOOR_BREAK = 144      # 跌破=箱型破
BUY_LO, BUY_HI = 150, 152   # 下緣買進區
SELL_LO, SELL_HI = 188, 194 # 上緣賣出區
BREAKOUT = 194         # 突破區

RECENT_BREACH_DAYS = 5  # 只看得到「當下」這一秒有沒有破線,沒有記憶,所以額外查最近幾天收盤有沒有破過

def get_price_and_volume():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="2mo", auto_adjust=False)
    vol = df['Volume'].iloc[-1]
    vol_ma20 = df['Volume'].rolling(20).mean().iloc[-1]
    price = float(df['Close'].iloc[-1])
    recent_closes = df['Close'].iloc[-RECENT_BREACH_DAYS:]
    recent_breach = bool((recent_closes <= FLOOR_BREAK).any())
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, vol, vol_ma20, recent_breach

def judge(price, vol, vol_ma20, recent_breach=False):
    vol_ratio = vol / vol_ma20 if vol_ma20 else 0
    breach_note = (f"　⚠️最近{RECENT_BREACH_DAYS}天內收盤曾經跌破144過(箱型已經破過一次，"
                   f"不是穩穩守在箱型裡，這次的反彈要留意是不是真的止穩)" if recent_breach else "")
    if price <= FLOOR_BREAK:
        return f"⛔ {price} 跌破 144（季線）— 箱型破了，停手、來回做先收手，重新評估趨勢。"
    if price < BUY_HI:
        return f"🟢 {price} 進入下緣買進區（{BUY_LO}~{BUY_HI}）— 機動倉分批接，靠近 144 加重。{breach_note}"
    if price < SELL_LO:
        zone = "偏下" if price < 170 else "偏上"
        return f"⚪ {price} 箱型中間（{zone}）— 上下都沒到，按兵不動，別在中間追加。{breach_note}"
    if price < BREAKOUT:
        return f"🔴 {price} 進入上緣賣出區（{SELL_LO}~{SELL_HI}）— 機動倉分批減，核心倉先留著看會不會突破。"
    # >= 194 突破
    if vol_ratio >= 1.5:
        return (f"🚀 {price} 帶量突破 194！（量是均量 {vol_ratio:.1f} 倍）"
                f"— 真突破，箱型操作失效，讓核心倉跑、別賣在起漲。")
    else:
        return (f"⚠️ {price} 突破 194 但量沒出來（僅均量 {vol_ratio:.1f} 倍）"
                f"— 假突破風險高，別追，留意是否拉回。")

def run():
    price, vol, vol_ma20, recent_breach = get_price_and_volume()
    print(f"=== {NAME}({SYMBOL}) 箱型關卡 ===")
    print(f"市價：{price}")
    print(judge(price, vol, vol_ma20, recent_breach))
    print(f"\n關卡備忘：144破線停手 / 150-152買 / 188-194賣 / 194帶量突破跑")

if __name__ == "__main__":
    run()
