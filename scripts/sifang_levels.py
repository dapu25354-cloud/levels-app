"""
是方(6561) 全帳走勢最弱/汰弱換強盯著 關卡監控
------------------------------------------------------------
背景:目前全庫存【走勢最弱、最落後】的一檔——空頭(月、季雙負、跌破20及60日線、RSI低)。
     注意:這裡的「弱」是【走勢方向在跌、相對大盤落後】,不是「低波動的死股」。
     是方是【淺碟、低量、但高波動】的股——量小推得動,漲能噴 70~80,跌也一樣快
     (381→316 就是 -65 點/-17% 的大波動,只是這次朝下)。淺碟高波動=兩個方向都又快又猛,
     所以「留倉觀察哨」比一般股更值得留(真轉向時彈得快、吃得到)。
     2026/07/01 殺到 316(長下影止跌低點)後反彈,且外資 17 天來首日買超(+29張)= 最大賣壓止血。
策略:汰弱換強第一順位,這檔是【要換掉/賣出】的,不是要買的。等反彈(彈向 344~350
     或站回20日線)掛限價賣、把錢換到強股;別在空頭中段殺最低,更別想不開往下攤平。

賣法(怕賣飛就分批):7~8成彈到 344~350 出、留 2~3成當觀察哨。
升級條件(才考慮多留那口):外資「連買 2~3 天」+ 價「站穩 20MA 345」兩者同時 → 才算真轉強。
下車底線:摜破 316(止跌低點)= 創新低更弱,剩的也走、不凹。

關卡(均線即時算):
  突破季高 = 真的轉強(難得)
  站回20MA = 原本最弱的有止跌跡象,可留意
  20MA下、60MA上 = 弱勢整理,等站回20MA才有戲
  空頭(均線下) = 最弱,汰弱換強第一順位,別接刀
  外資追蹤 = 每天自動抓近6日外資買賣超,看「首買」有沒有變「續買」
"""
import sys
import yfinance as yf
import requests
from datetime import datetime, timedelta, timezone

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SYMBOL = "6561.TWO"
NAME = "是方"
CODE = "6561"                 # 純代號(抓籌碼用)
LOW_PIVOT = 316              # 2026/07/01 止跌低點,摜破=創新低更弱
SELL_LO, SELL_HI = 344, 350  # 反彈賣區(貼20MA)
TW_TZ = timezone(timedelta(hours=8))


def get_data():
    tk = yf.Ticker(SYMBOL)
    df = tk.history(period="4mo", auto_adjust=False)
    if df.empty:
        df = yf.Ticker("6561.TW").history(period="4mo", auto_adjust=False)
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


def _foreign_net_tpex(t_date):
    """某天是方的外資買賣超(張);抓不到回 None。(櫃買股走 TPEx)"""
    try:
        y = int(t_date[:4]) - 1911
        d_fmt = f"{y}/{t_date[4:6]}/{t_date[6:]}"
        url = ("https://www.tpex.org.tw/web/stock/3insti/daily_trade/"
               f"3itrade_hedge_result.php?l=zh-tw&o=json&se=EW&t=D&d={d_fmt}")
        resp = requests.get(url, timeout=12).json()
        rows = (resp.get('tables') or [{}])[0].get('data') or []
        for row in rows:
            if str(row[0]).strip() == CODE:
                return int(str(row[10]).replace(',', '') or 0) // 1000
    except Exception:
        return None
    return None


def foreign_recent(days=6):
    """近幾個交易日外資買賣超(張),舊->新。抓不到就跳過那天。"""
    out = []
    now = datetime.now(TW_TZ)
    d_offset = 0
    while len(out) < days and d_offset < days * 3:
        t_date = (now - timedelta(days=d_offset)).strftime('%Y%m%d')
        net = _foreign_net_tpex(t_date)
        if net is not None:
            out.append((t_date, net))
        d_offset += 1
    return list(reversed(out))


def foreign_line(data):
    """把外資近況組成一行字 + 一句判斷。"""
    if not data:
        return "外資:TPEx 資料抓不到(可能今日未更新),下次再追。"
    seq = "  ".join(f"{n:+d}" for _, n in data[:-1]) + f"  [{data[-1][1]:+d}今]"
    today = data[-1][1]
    prior = [n for _, n in data[:-1]]
    if today > 0:
        streak = 0
        for _, n in reversed(data):
            if n > 0:
                streak += 1
            else:
                break
        if streak == 1 and prior and all(n <= 0 for n in prior):
            verdict = f"外資由賣轉買(前{len(prior)}日皆賣)= 止血訊號,關鍵看『明後天續不續買』,別當反轉。"
        else:
            verdict = f"外資連買 {streak} 天 = 買盤延續中;配合站穩月線才算真轉強。"
    elif today < 0:
        verdict = "外資今日仍賣 = 賣壓未止,反彈是拿來減的、別接刀。"
    else:
        verdict = "外資今日持平,方向未明。"
    return f"外資近{len(data)}日(張): {seq}\n   → {verdict}"


def judge(price, ma20, ma60, high60, vol=None, vol_ma20=None):
    if price >= ma20:
        if price >= high60 * 0.99:
            return f"🟢 {price} 突破季高({high60:.0f}) — 真的轉強了,難得,可續抱/留意。"
        return f"🟢 {price} 站回月線({ma20:.0f}) — 原本最弱的有止跌轉強跡象,可留意。"
    if price >= ma60:
        return f"🟡 {price} 月線({ma20:.0f})下、季線上 — 弱勢整理,等站回 {ma20:.0f} 才有戲、別追。"
    return (f"⚠️ {price} 空頭、全帳走勢最弱(月季雙負;淺碟高波動非牛皮) — 汰弱換強第一順位,這檔是【要賣掉的】。"
            f"等反彈(彈向{SELL_LO}~{SELL_HI}或站回月線{ma20:.0f})掛限價賣;不是買點,別往下攤、別想搶反彈買。")


def run():
    price, ma20, ma60, high60, vol, vol_ma20 = get_data()
    vdesc, _ = vol_desc(vol, vol_ma20)
    print(f"=== {NAME}({SYMBOL}) 全帳走勢最弱/汰弱換強盯著（淺碟高波動、非牛皮股）===")
    print(f"市價：{price}    月線：{ma20:.0f}    季線：{ma60:.0f}    季高：{high60:.0f}    止跌低點：{LOW_PIVOT}")
    print(f"成交量：{vdesc}")
    print(judge(price, ma20, ma60, high60))
    print("   " + foreign_line(foreign_recent()))
    print(f"\n備忘：這檔要賣不要買 / 反彈{SELL_LO}~{SELL_HI}分批減(留一口觀察) / "
          f"升級要『外資連買+站穩345』/ 破{LOW_PIVOT}創新低就走 / 汰弱換強第一順位")


if __name__ == "__main__":
    run()
