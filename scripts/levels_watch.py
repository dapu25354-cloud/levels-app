"""
關卡小白 — 一次看完所有「在盯關卡」的持股(分流版)
------------------------------------------------------------
看花了問題的解法:不再一口氣印一整面牆。改成「分流」:
  🔔 要你動的(過熱賣強 / 跌破均線 / 轉弱)→ 印完整細節
  🟢 接近突破的 → 印一行
  😴 抱著沒事的 → 只報名字,不吵你
最後才把「要你動的」完整細節列在下面。掃一眼上面就知道今天要不要動手。

要新增股票:照 wistron_levels.py / zhongxin_levels.py 的格式寫一個 xxx_levels.py
           (run() 要印一行 === 名稱(代號) ... === 和一行開頭是表情符號的判斷),
           然後在下面 MODS 加進來即可。
"""
import sys
import io
import re
import contextlib
import yfinance as yf
import positions_store

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import wistron_levels
import delta_levels
import yuanta_levels
import zhishen_levels
import junhua_levels
import shijie_levels
import shunda_levels
import shihe_levels
import tsmc_levels
import zhongxin_levels
import dalight_levels
import evaair_levels
import csteel_levels
import guopiao_levels
import sifang_levels
import advantech_levels
import wiwynn_levels
import taishin_levels
import taiwan50_levels
import lianjun_levels
import fanyuan_levels
import ruize_levels
import baocheng_levels
import tongyishi_levels
import zuanquan_levels
import tongyichao_levels

MODS = [wistron_levels, delta_levels, yuanta_levels,
        zhishen_levels, junhua_levels, shijie_levels, shunda_levels,
        shihe_levels, tsmc_levels, zhongxin_levels, dalight_levels,
        evaair_levels, csteel_levels, guopiao_levels, sifang_levels,
        advantech_levels, wiwynn_levels, taishin_levels, taiwan50_levels,
        lianjun_levels,
        fanyuan_levels, ruize_levels, baocheng_levels, tongyishi_levels,
        zuanquan_levels, tongyichao_levels]
# 註(2026-07-11更新):上詮/華星光/日月光投控 這3檔CPO觀察名單她要求也併進 watch_list.json 一起管,
#    不再各管各的。但它們「尚未持有」,不能套通用規則(會被誤判成持有)——下面兜底邏輯
#    會認出這3檔、改用 generic_levels.CPOWatchLevels(重用 cpo_watch.py 的判斷,強制標「空手」)。

# 2026-07-11:自動兜底,直接對 watch_list.json 補漏——統一超登記在名冊裡卻沒人接客製腳本、
# 被完全漏掃過一次。凡是 watch_list.json 有登記但上面 MODS 沒手動接的代號,自動用
# generic_levels.py 的通用規則掃一遍(不算精細,但至少不會再無聲無息漏掉);
# 之後想幫哪一檔升級成客製版,寫 xxx_levels.py 接進 MODS 就會自動蓋過這支通用版。
import json
import os
import generic_levels

def _add_watchlist_fallbacks():
    covered = {getattr(m, "SYMBOL", None) for m in MODS}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watch_list.json")
    try:
        items = json.load(open(path, encoding="utf-8"))
    except Exception:
        return
    try:
        import cpo_watch
        cpo_roles = {code: (name, role) for code, name, role in cpo_watch.WATCH}
    except Exception:
        cpo_roles = {}
    for it in items:
        sym, nm = it.get("symbol"), it.get("name")
        if sym and nm and sym not in covered:
            if sym in cpo_roles:
                _, role = cpo_roles[sym]
                MODS.append(generic_levels.CPOWatchLevels(sym, nm, role))
            else:
                MODS.append(generic_levels.GenericLevels(sym, nm))
            covered.add(sym)

_add_watchlist_fallbacks()

# 2026-07-11:輸出順序比照 watch_list.json 的排法(上市.TW在前、上櫃.TWO在後,各自依代號排序)。
# 排序用 SYMBOL 直接算,不用手動排 import/MODS 清單——以後加新股票、順序永遠自動跟著對。
def _sym_key(m):
    sym = getattr(m, "SYMBOL", None) or "9999.ZZZ"
    code, _, suf = sym.partition(".")
    return (suf, code)

MODS.sort(key=_sym_key)

# 表情符號 -> 嚴重度(數字越大越要你注意)。新增模組若用了新符號,記得在這補上,
# 否則會被當「沒事」漏接(汎銓的⛔就曾這樣被埋掉)。
SEVERITY = {
    '⛔': 3,   # 一次出清 / 別追高 — 最該動手
    '⚠️': 3,   # 跌破季線、轉弱、汰弱
    '🔴': 2,   # 過熱賣強
    '🚀': 2,   # 反彈收復、賣最後一批鎖利
    '🟡': 2,   # 跌破月線、回檔留意
    '🟩': 2,   # 上車訊號2(帶量大紅K)= 可以小量試接,要你動手
    '🟢': 1,   # 接近突破 / 扎實支撐好買點 / 上車訊號1(開始盯)
    '⏸': 1,    # 縮手、暫緩加碼
    '⚪': 0,   # 抱著沒事
}

def _parse(text):
    """從 run() 的輸出抓出 名稱、判斷行、嚴重度、表情、市價。"""
    name, verdict, sev = '?', '', 0
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('===') and '(' in s:
            name = s.split('===')[1].split('(')[0].strip()
        for emo, score in SEVERITY.items():
            if s.startswith(emo):
                if score >= sev:
                    sev, verdict = score, s
    emoji = verdict.split(' ', 1)[0] if verdict else ''
    pm = re.search(r'\d+(?:\.\d+)?', verdict)
    price = float(pm.group()) if pm else 0.0
    return name, verdict, sev, emoji, price

def _fmtp(p):
    """低價股留小數,高價股取整(限價單要報得準)。"""
    return f"{p:.1f}" if p < 100 else f"{round(p)}"

def order_hint(name, emoji, price):
    """把訊號翻成『開盤前可掛的限價單』。沒有明確動作就回 None(=抱著/留意,不掛單)。"""
    # 固定計畫(她的策略,跟今天訊號無關)
    if name == '均華':
        # 好公司被族群估值殺、基本面沒壞 → 抱住別動、別往下攤,不是出清!
        # (它的⛔是「跌破前低停手」之意,不可套用通用⛔的「出清」)
        return None
    if name == '是方':
        target = positions_store.get_lot_full('6561.TWO').get('target_sell')
        if target:
            return f"想換掉 → 反彈掛 限價賣 {target}（汰弱換強；到價自動賣、別再凹別加）"
        return None
    if name == '長榮航':
        # 已出清,空手等接回。包袱已甩、本金落袋,沒部位=不掛單。
        return None
    if name == '緯創':
        # 它的⛔是箱型策略的「跌破144停手、重新評估趨勢」,不是「出清持股」,
        # 不可套用通用⛔的「出清」文字(這支也沒追蹤COST/SHARES,不是持倉部位)。
        return None
    # 依今天訊號(動態)
    if emoji == '🟩':
        return "上車訊號2亮了 → 小量試接（先接一點、別一次全押；接回後守住該檔停損,跌破再走）"
    if emoji == '⛔':
        return "掛 限價賣 出清（到價自動賣、別零碎砍）"
    if emoji == '🚀':
        return "賣最後一批鎖利 → 掛在『實際高價』(看盤軟體為準,別掛低於現價)"
    if emoji == '🔴':
        # 注意:yfinance(尤其櫃買股)價會慢半拍,別用工具價當賣價、別掛低於市價、別把漲停飆股賣太早
        return ("賣強鎖利一部分 → 掛在『實際高價』(以看盤軟體為準,工具價會慢半拍、別掛低於現價)；"
                "漲停/急噴中先讓它跑,別急著全賣。核心不動")
    return None

def fetch_changes(symbols):
    """一次批次抓所有股票的今天漲跌%(只打一個網路呼叫,不拖慢工具)。
    回傳 {代號: 漲跌%};抓不到的那檔給 None,不讓它擋住整份報告。"""
    changes = {s: None for s in symbols}
    try:
        data = yf.download(symbols, period="7d", auto_adjust=False,
                           progress=False, group_by="ticker")
    except Exception:
        return changes
    for s in symbols:
        try:
            if len(symbols) == 1:
                closes = data["Close"].dropna()
            else:
                closes = data[s]["Close"].dropna()
            if len(closes) >= 2:
                changes[s] = (float(closes.iloc[-1]) / float(closes.iloc[-2]) - 1) * 100
        except Exception:
            pass
    return changes

def day_tag(chg):
    """給明細/清單用的今日漲跌標記;大漲大跌先跳出來,別被落後的均線判斷蓋掉。"""
    if chg is None:
        return ""
    if chg >= 5:
        return f"🔺今日噴出 {chg:+.1f}%"
    if chg <= -5:
        return f"🔻今日急殺 {chg:+.1f}%"
    return f"今日 {chg:+.1f}%"

def day_mark(chg):
    """給『抱著沒事』那排用的精簡標記:只有大漲大跌才貼,免得整排都是數字。"""
    if chg is None:
        return ""
    if chg >= 5:
        return f"🔺{chg:+.0f}%"
    if chg <= -5:
        return f"🔻{chg:+.0f}%"
    return ""

def collect():
    """掃全部持股、分流成 flagged/breakout/empty/calm/errors/orders，不印出——給自動化腳本(如午餐小抄)用。
    run() 是這份資料的『印出來』版本，兩邊共用同一份掃描，不會兜出不一致的數字。"""
    flagged, breakout, calm, empty, errors, orders = [], [], [], [], [], []
    symbols = [getattr(m, "SYMBOL", None) for m in MODS]
    changes = fetch_changes([s for s in symbols if s])
    for mod in MODS:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                mod.run()
            text = buf.getvalue()
        except Exception as e:
            errors.append((mod.__name__, str(e)))
            continue
        name, verdict, sev, emoji, price = _parse(text)
        chg = changes.get(getattr(mod, "SYMBOL", None))
        # 空手等接回的股(標題有「空手」)單獨一類,別跟「抱著持有」的混在一起,
        # 否則 ⚪ 會被丟進「抱著沒事」=誤導成你還持有(銳澤就這樣矛盾過)。
        is_empty = '空手' in text
        if is_empty:
            empty.append((name, verdict, chg))
        elif sev >= 2:
            flagged.append((name, verdict, text, chg))
        elif sev == 1:
            breakout.append((name, verdict, chg))
        else:
            calm.append((name, chg))
        # 空手(沒部位)別套用 order_hint——它是為「有部位」設計的賣出/出清建議,
        # 空手股的🔴/🚀只是「還過熱別追/轉強可小接」的參考語氣,不是可掛的賣單
        # (曾經統一超已全數出清還被列進「開盤前掛好的限價單」叫她賣強鎖利,是誤導)。
        if not is_empty:
            oh = order_hint(name, emoji, price)
            if oh:
                orders.append((name, oh))
    return {"flagged": flagged, "breakout": breakout, "empty": empty,
            "calm": calm, "errors": errors, "orders": orders}


def run():
    d = collect()
    flagged, breakout, empty, calm, errors, orders = (
        d["flagged"], d["breakout"], d["empty"], d["calm"], d["errors"], d["orders"])

    print("######### 關卡小白 — 今天要不要動手 #########\n")

    def _line(name, verdict, chg):
        tag = day_tag(chg)
        return f"   {name}　{verdict}" + (f"　［{tag}］" if tag else "")

    if flagged:
        print(f"🔔 要你注意的({len(flagged)}檔)：")
        for name, verdict, _, chg in flagged:
            print(_line(name, verdict, chg))
    else:
        print("🔔 要你注意的：無 — 今天沒人破關卡,輕鬆。")

    if breakout:
        print(f"\n👀 順便看一眼({len(breakout)}檔)：")
        for name, verdict, chg in breakout:
            print(_line(name, verdict, chg))

    if empty:
        print(f"\n🫙 空手等接回({len(empty)}檔；沒醒別碰、別接刀)：")
        for name, verdict, chg in empty:
            print(_line(name, verdict, chg))

    if calm:
        movers = [f"{n}{day_mark(c)}" for n, c in calm]
        print(f"\n😴 抱著沒事的({len(calm)}檔)：" + "、".join(movers))
        big = [f"{n} {c:+.1f}%" for n, c in calm if c is not None and abs(c) >= 5]
        if big:
            print("   ⚠️ 這排裡今天有大動作的:" + "、".join(big) + " — 抱著沒事但別忽略,點開看一下。")

    if errors:
        print(f"\n❓ 抓不到資料({len(errors)}檔)：" + "、".join(n for n, _ in errors))

    if orders:
        print(f"\n📌 今天可掛的單(限價單；開盤前掛好、到價自動成交,不用盯盤)：")
        for name, oh in orders:
            print(f"   {name}　{oh}")
        print("   ※沒到價=沒成交,不是壞事(代表沒到你的價,本來就別追)。其餘沒列的就是抱著、不掛單。")

    if flagged:
        print("\n────────── 要你注意的,細節在這 ──────────")
        for name, verdict, text, chg in flagged:
            print()
            print(text.rstrip())
            tag = day_tag(chg)
            if tag:
                print(f"　→ {tag}")

    print("\n######### 完 #########")

if __name__ == "__main__":
    run()
