"""
台達電(2308) 加碼/持有 關卡監控
------------------------------------------------------------
背景:以第二證券商(低手續費戶)為準,分批加碼中,加權平均法(非FIFO,賣出不動均價、只有買進才重算)。
     提醒:券商是FIFO、這支程式是簡單加權平均,長期會跟券商實際成本產生落差,
     要靠實際成交明細截圖才能校正,不能單靠這支程式自己算的均價往下走。
     原第一券商還有一筆更早、更低成本的核心不列入這裡管理。
     台達電±10%狂晃,用緊停損加碼老是被洗掉。對策:長線心態分批接、別設緊停損。
成本/股數/是否加滿(FULLY_ADDED):見 app 內持倉管理(不寫死於程式碼)。

兩段邏輯(用 FULLY_ADDED 切換):
  ● 還沒加滿(FULLY_ADDED=False):
      - 貼近近3個月實測低點 = 回檔買弱區,分批接
      - 跌破近3個月實測低點 = 第二批暫緩,等站穩(這才叫「縮手」=還沒花的錢先收著)
      - 2350以上 = 別追高,等回檔
  ● 已加滿(FULLY_ADDED=True):
      - 1750以上 = 沒事,抱著,±10%雜訊不理(長線倉)
      - 跌破1750 = 才警告:長線趨勢轉弱,配合基本面(AI電源訂單)是否裂,考慮「減碼」非清倉

2026-07-17教訓:接點/暫緩線本來是寫死的數字,抓到這種寫死的關卡會過時
(舊數字容易變成「叫她等漲更高才買」，跟新測到的真低點自相矛盾)。改成每次執行都自動抓
「近3個月實際最低點」當支撐基準，不用再手動更新這幾個數字。CHASE(別追高)、TREND_BREAK(長線趨勢警戒)
這兩個是策略性的固定關卡、不是短期支撐,不受這次改動影響,還是固定值。
"""
import sys
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "2308.TW"
NAME = "台達電"

COST, SHARES = positions_store.get_lot(SYMBOL)
FULLY_ADDED = bool(positions_store.get_lot_full(SYMBOL).get("fully_added", False))  # app 內持倉管理可改

# 關卡(策略性固定值,不隨股價區間平移,見上面說明)
CHASE = 2350                 # 以上別追高
TREND_BREAK = 1750           # 加滿後才看:跌破=長線趨勢警戒

def get_price():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="3mo", auto_adjust=False)
    price = float(df['Close'].iloc[-1])
    ma60 = float(df['Close'].rolling(60).mean().iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    recent_low = float(df['Low'].min())  # 近3個月實測低點,當「扎實接點」的基準,每次執行自動抓新的、不用手動改
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma60, vol, vol_ma20, recent_low

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

def judge_not_added(price, recent_low):
    hold_gate = recent_low
    add_lo, add_hi = recent_low, recent_low * 1.04  # 低點~低點+4%緩衝,當扎實接點區
    if price >= CHASE:
        return f"⛔ {price} 偏高(>{CHASE})— 別追高,等它回檔到買弱區再接。"
    if price < hold_gate:
        return (f"⏸ {price} 跌破近3個月低點 {hold_gate:.0f} — 第二批暫緩(這才是「縮手」:沒花的錢先收著),"
                f"等它站穩 {hold_gate:.0f} 再接,別往下追刀。")
    if price <= add_hi:
        return f"🟢 {price} 靠近扎實支撐區（{add_lo:.0f}~{add_hi:.0f}，近3個月實測低點）— 分批接的好點,長線心態、別設緊停損。"
    return (f"🟡 {price} 回檔買弱區（{hold_gate:.0f}~{CHASE}）— 可分批接第一批;"
            f"想更扎實就等摸到近3個月低點附近({add_lo:.0f}~{add_hi:.0f})再接第二批。中間別一次梭。")

def judge_added(price):
    if price > TREND_BREAK:
        return (f"⚪ {price} 在 {TREND_BREAK} 之上 — 沒事,抱著。±10%晃動是台達電常態,"
                f"長線心態,雜訊不理它。(距趨勢線還有 {price-TREND_BREAK:.0f} 點)")
    return (f"⚠️ {price} 跌破長線趨勢 {TREND_BREAK} — 該認真看了:配合基本面(AI電源訂單/輝達平台/800V進度)"
            f"是否真的裂。若基本面也壞→考慮『減碼』(不是清倉);只是價格雜訊就續抱。")

def run():
    price, ma60, vol, vol_ma20, recent_low = get_price()
    vdesc, _ = vol_desc(vol, vol_ma20)
    if SHARES:
        state = f"第二證券商戶:現{SHARES}股,均價約{COST}" if FULLY_ADDED else f"尚未加滿(現{SHARES}股,均價約{COST})"
    else:
        state = "空手"
    print(f"=== {NAME}({SYMBOL}) 關卡監控 ===")
    print(f"市價：{price}    季線：{ma60:.0f}    狀態：{state}")
    print(f"成交量：{vdesc}")
    print(judge_added(price) if FULLY_ADDED else judge_not_added(price, recent_low))
    if not FULLY_ADDED:
        print(f"\n備忘：貼近近3個月低點({recent_low:.0f})扎實接 / 跌破{recent_low:.0f}第二批暫緩 / {CHASE}以上別追 / 加滿後在app把 fully_added 改 True")
    else:
        print(f"\n備忘：1750以上無腦抱 / 跌破1750才看基本面決定減不減")

if __name__ == "__main__":
    run()
