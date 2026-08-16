"""
通用備用關卡判斷 —— 給 watch_list.json 裡「還沒手動寫 xxx_levels.py 客製」的股票自動兜底用。
------------------------------------------------------------
背景(2026-07-11)：統一超已經登記在 watch_list.json，卻沒人幫它寫客製腳本，
結果關卡小白完全沒掃到它，直到她自己發現才補上。以後不想再漏掉任何一檔。

做法：levels_watch.py 會自動比對 watch_list.json 的股票清單跟 MODS 已涵蓋的代號，
凡是「有登記但沒客製腳本」的，用這支的通用規則(月線/季線/RSI)自動產生一份最陽春判斷，
確保至少不會被完全漏掉；沒有成本/持股資訊，所以不算「賣強鎖利」這類要她操作的細節。
想幫哪一檔升級成完整客製版，照格式寫一支 xxx_levels.py 接進 levels_watch.py 的 MODS 即可，
客製版永遠蓋過這支通用版(因為已經在 MODS 裡的優先，不會重複掃)。
"""
import sys
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def rsi(close, window=14):
    delta = close.diff()
    up = delta.clip(lower=0).rolling(window).mean()
    down = -delta.clip(upper=0).rolling(window).mean()
    rs = up / down
    return 100 - (100 / (1 + rs))


TOL = 0.01


def _judge(price, ma20, ma60, high60, rs14):
    if price < ma60 * (1 - TOL):
        return f"⚠️ {price} 空手；跌破季線({ma60:.1f}) — 轉弱,留意(通用規則,尚未客製,建議請她確認要不要幫它寫專用腳本)。"
    if price < ma20 * (1 - TOL):
        return f"🟡 {price} 空手；跌破月線({ma20:.1f}) — 回檔,守季線({ma60:.1f})(通用規則,尚未客製)。"
    if rs14 >= 70 and price >= high60 * 0.98:
        return f"🔴 {price} 空手；過熱貼高(RSI {rs14:.0f}) — 別追高,等拉回再說(通用規則,尚未客製,沒有成本資料無法算損益)。"
    return f"⚪ {price} 空手；健康(月線 {ma20:.1f}上、RSI {rs14:.0f}) — 沒訊號,沒醒別碰(通用規則,尚未客製)。"


class GenericLevels:
    """假裝成一支 xxx_levels.py 模組，讓 levels_watch.py 可以直接塞進 MODS 一視同仁地掃。
    watch_list.json 裡沒手動客製腳本的股票，一律當「空手觀察」處理(不知道有沒有持股，
    不能亂猜她有持倉——2026-07-13 踩過廣達/先進光被通用規則誤標成「抱著沒事」的坑，
    因為舊版輸出不含「空手」關鍵字，被levels_watch.py的分類邏輯誤丟進抱著持有那類)。
    想追蹤實際持股/成本，寫一支專屬 xxx_levels.py 接進 MODS 即可蓋過這支通用版。"""

    def __init__(self, symbol, name):
        self.SYMBOL = symbol
        self.NAME = name

    def run(self):
        try:
            tk = yf.Ticker(self.SYMBOL)
            df = tk.history(period="4mo", auto_adjust=False)
            if df.empty or len(df) < 20:
                print(f"=== {self.NAME}({self.SYMBOL}) 通用關卡(空手,尚未客製) ===")
                print(f"⚪ 空手；抓不到足夠資料,略過(通用規則,尚未客製)。")
                return
            c = df['Close']
            price = float(c.iloc[-1])
            ma20 = float(c.rolling(20).mean().iloc[-1])
            ma60 = float(c.rolling(60).mean().iloc[-1]) if len(c) >= 60 else ma20
            high60 = float(c.iloc[-60:].max())
            rs14 = float(rsi(c).iloc[-1])
            try:
                info = tk.info
                rp = info.get('regularMarketPrice') or info.get('currentPrice')
                if rp:
                    price = float(rp)
            except Exception:
                pass
            print(f"=== {self.NAME}({self.SYMBOL}) 通用關卡(空手,尚未客製) ===")
            print(f"市價：{price}    月線：{ma20:.1f}    季線：{ma60:.1f}    季高：{high60:.1f}    RSI：{rs14:.0f}")
            print(_judge(price, ma20, ma60, high60, rs14))
            print(f"\n備忘：這是自動兜底的通用規則(不確定有沒有持股，一律當空手觀察)，不是為這檔量身寫的關卡；"
                  f"想要客製化(記成本、專屬策略)可以請她說一聲。")
        except Exception as e:
            print(f"=== {self.NAME}({self.SYMBOL}) 通用關卡(空手,尚未客製) ===")
            print(f"⚪ 空手；抓取失敗({e})，略過。")


class CPOWatchLevels:
    """CPO觀察名單(華星光/上詮/日月光投控)的橋接版——這幾檔『尚未持有』，
    不能套用上面的通用規則(會被誤判成持有部位)。直接重用 cpo_watch.py 既有的
    analyze()/signal()判斷邏輯，只是包成 levels_watch.py 認得的格式，
    且輸出文字裡一定含「空手」關鍵字，確保被分進「空手等接回」而不是持股類。"""

    def __init__(self, symbol, name, role=""):
        self.SYMBOL = symbol
        self.NAME = name
        self.role = role

    def run(self):
        import cpo_watch
        print(f"=== {self.NAME}({self.SYMBOL}) CPO觀察(空手,尚未持有) ===")
        try:
            a = cpo_watch.analyze(self.SYMBOL)
            if not a:
                print("⚪ 空手；抓取失敗，略過。")
                return
            price, ma20, ma60, high60, rs14, chg = a
            print(f"市價：{price:.1f}    月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    RSI：{rs14:.0f}    {cpo_watch.day_tag(chg)}")
            if self.role:
                print(f"題材：{self.role}")
            sig = cpo_watch.signal(price, ma20, ma60, high60, rs14, chg)
            emoji, _, rest = sig.partition(' ')
            print(f"{emoji} 空手；{rest}")
        except Exception as e:
            print(f"⚪ 空手；抓取失敗({e})，略過。")
