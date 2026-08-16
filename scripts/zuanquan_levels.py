# -*- coding: utf-8 -*-
"""
鑽全(1527) 觀察關卡 — 空手觀察，不是持股。
賭「美國降息→房市回溫→訂單回來」的轉機波段。過去是死水(牛皮盤整)，
2026/07/04 出現爆量站上均線的發動前兆，但要確認：
   站穩34帶量 = 真發動，可小量試單、停損33
   跌破33量縮 = 發動失敗、回死水，別碰別接刀
一天爆量不算數，看量價確認 > 看小型股不穩的EPS預估。
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "1527.TW"
NAME = "鑽全"
TRIGGER = 34.0   # 站穩帶量 = 發動
FALLBACK = 33.0  # 跌破 = 回死水 / 停損


def run():
    try:
        t = yf.Ticker(SYMBOL)
        df = t.history(period="3mo")
        c = df['Close']
        v = df['Volume']
        price = float(c.iloc[-1])
        vr = float(v.iloc[-1] / v.rolling(20).mean().iloc[-1])
        amp10 = (float(c.iloc[-10:].max()) - float(c.iloc[-10:].min())) / float(c.iloc[-10:].min()) * 100
        # 顯示用真實市價(避免還原價偏差)，抓不到就用收盤
        try:
            rp = t.info.get('regularMarketPrice')
            if rp:
                price = float(rp)
        except Exception:
            pass
    except Exception as e:
        print(f"=== {NAME}({SYMBOL}) 抓不到資料：{e} ===")
        return

    print(f"=== {NAME}({SYMBOL}) 空手觀察 現價 {price:.1f} 量比 {vr:.1f} 近10日振幅 {amp10:.1f}% ===")

    if price >= TRIGGER and vr >= 1.3:
        print(f"🟩 發動訊號：站穩{TRIGGER:.0f}又帶量({vr:.1f}倍)→ 轉機波段可小量試單、停損{FALLBACK:.0f}。"
              f"賭美國降息/房市回溫，別重壓、別當長抱。")
    elif price >= TRIGGER:
        print(f"🟢 站上{TRIGGER:.0f}但量沒跟({vr:.1f}倍)→ 只算半個發動，等帶量確認再動，別追。")
    elif price >= FALLBACK:
        print(f"🟢 醞釀中：卡在{FALLBACK:.0f}-{TRIGGER:.0f}，站穩{TRIGGER:.0f}帶量才算真發動，先盯著別急。")
    else:
        print(f"⚪ 回死水：跌破{FALLBACK:.0f}、發動失敗，繼續躺，別碰別接刀。")


if __name__ == "__main__":
    run()
