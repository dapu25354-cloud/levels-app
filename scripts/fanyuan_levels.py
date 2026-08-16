"""
汎銓(6830) 空手等接回 關卡監控 —— 空手版
------------------------------------------------------------
背景:汎銓從季高腰斬,曾在高檔出清過(賣對了)。之後分批零股試接、全數賣強鎖利過一次(完美示範)。
     同日又心急接刀(老毛病)套牢,隔天照停損紀律出清(小虧,但守住紀律、沒往下攤)。
     → 現在【已全數清空、空手】,留在雷達盯,不再產生賣單。
策略:空手觀望。想接回要等站回20日線的止跌訊號,別在破線趨勢裡接刀。

關卡(均線即時算):
  還沒止穩(20MA下)   = 空手觀望,別接刀
  站回20日線         = 止跌跡象,可小量試接回
  站上60日線         = 轉強,可考慮加、拉回不破再加
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "6830.TW"
NAME = "汎銓"

def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    c = df['Close']
    price = float(c.iloc[-1])
    ma20 = float(c.rolling(20).mean().iloc[-1])
    ma60 = float(c.rolling(60).mean().iloc[-1])
    vol = float(df['Volume'].iloc[-1])
    vol_ma20 = float(df['Volume'].rolling(20).mean().iloc[-1])
    try:
        info = tk.info
        rp = info.get('regularMarketPrice') or info.get('currentPrice')
        if rp:
            price = float(rp)
    except Exception:
        pass
    return price, ma20, ma60, vol, vol_ma20

def vol_desc(vol, vol_ma20):
    ratio = vol / vol_ma20 if vol_ma20 else 1.0
    tag = "放量" if ratio >= 1.5 else ("量縮" if ratio <= 0.5 else "量平")
    return f"{tag}(今日{vol:,.0f}股，是20日均量的{ratio*100:.0f}%)", ratio

TOL = 0.01
def judge(price, ma20, ma60, vol=None, vol_ma20=None):
    if price < ma20 * (1 - TOL):
        return f"⚪ {price:.0f} 空手；還在月線({ma20:.0f})下打底 — 沒站穩,別接刀,等站回月線再看。"
    if price < ma60 * (1 - TOL):
        return f"🟢 {price:.0f} 空手；站回月線({ma20:.0f}) — 止跌跡象,可小量試接回(別追、別重押)。"
    return f"🚀 {price:.0f} 空手；站上季線({ma60:.0f})轉強 — 打底完成跡象,可考慮小量接回、拉回不破再加。"

def run():
    price, ma20, ma60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 空手等接回（接刀停損出場後）===")
    print(f"市價：{price:.0f}    月線：{ma20:.0f}    季線：{ma60:.0f}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60))
    print("\n備忘：已清空空手 / 別接刀 / 站回月線才小量試接 / 上次心急接刀套牢的教訓別重蹈")

if __name__ == "__main__":
    run()
