"""
關卡小白 App — Streamlit 版
------------------------------------------------------------
密碼閘門 + 總覽(沿用 levels_watch.collect() 原始邏輯，不重寫判斷) + 單檔深入 + 持倉管理。
真實成本/股數一律透過 positions_store 存取，不寫在這個 repo 的程式碼裡（見 scripts/positions_store.py）。
"""
import sys
import os
import io
import contextlib
from datetime import date

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))

import positions_store

st.set_page_config(page_title="關卡小白", page_icon="🎯", layout="centered")


def check_password():
    if st.session_state.get("authed"):
        return True
    st.title("🎯 關卡小白")
    pw = st.text_input("密碼", type="password")
    if pw:
        if pw == st.secrets.get("APP_PW"):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("密碼錯誤")
    return False


if not check_password():
    st.stop()


import levels_watch


@st.cache_data(ttl=120)
def _collect():
    return levels_watch.collect()


def _run_module(mod):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.run()
    return buf.getvalue()


st.title("🎯 關卡小白")
tab1, tab2, tab3 = st.tabs(["總覽", "單檔深入", "持倉管理"])

with tab1:
    if st.button("重新整理"):
        _collect.clear()
        st.session_state["dashboard_loaded"] = True
    if st.session_state.get("dashboard_loaded"):
        with st.spinner("抓取行情中，請稍候..."):
            d = _collect()
    else:
        st.info("尚未載入行情；若要查看總覽，請按上方「重新整理」。持股管理可以直接使用。")
        d = {"flagged": [], "breakout": [], "empty": [], "calm": [], "errors": [], "orders": []}
    flagged, breakout, empty, calm, errors, orders = (
        d["flagged"], d["breakout"], d["empty"], d["calm"], d["errors"], d["orders"])
    held_count = len({row["symbol"] for row in positions_store.holdings()})
    st.caption(f"持股判斷：{held_count} 檔有 shares；其餘才列入空手觀察。")

    def _line(name, verdict, chg):
        tag = levels_watch.day_tag(chg)
        return f"**{name}**　{verdict}" + (f"　［{tag}］" if tag else "")

    st.subheader(f"🔔 要你注意的（{len(flagged)}檔）")
    if flagged:
        for name, verdict, _text, chg in flagged:
            st.markdown(_line(name, verdict, chg))
    else:
        st.write("無 — 今天沒人破關卡，輕鬆。")

    if breakout:
        st.subheader(f"👀 順便看一眼（{len(breakout)}檔）")
        for name, verdict, chg in breakout:
            st.markdown(_line(name, verdict, chg))

    if empty:
        st.subheader(f"🫙 空手等接回（{len(empty)}檔）")
        for name, verdict, chg in empty:
            st.markdown(_line(name, verdict, chg))

    if calm:
        st.subheader(f"😴 抱著沒事的（{len(calm)}檔）")
        movers = [f"{n}{levels_watch.day_mark(c)}" for n, c in calm]
        st.write("、".join(movers))

    if orders:
        st.subheader("📌 今天可掛的單")
        for name, oh in orders:
            st.markdown(f"**{name}**　{oh}")

    if errors:
        st.caption("❓ 抓不到資料：" + "、".join(n for n, _ in errors))

with tab2:
    options = {f"{m.NAME}（{m.SYMBOL}）": m for m in levels_watch.MODS}
    choice = st.selectbox("選股票（31檔）", list(options.keys()), key="detail_choice")
    mod = options[choice]
    position = positions_store.get_position_summary(mod.SYMBOL)
    if position["is_held"]:
        st.success(
            f"判斷身分：已持股｜合計 {position['shares']:g} 股｜"
            f"加權平均成本 {position['cost']:g}"
        )
        st.caption("以下關卡建議以持股者情境閱讀；核心/機動未拆分時，先以總持股為準。")
    else:
        st.info("判斷身分：空手｜沒有任何倉位 shares > 0，以下使用等待進場情境。")
    if st.button("查看關卡判斷"):
        with st.spinner("抓即時資料中..."):
            text = _run_module(mod)
        st.text(text)

with tab3:
    source = positions_store.storage_info()
    write_hint = "Gist 優先；POSITIONS_JSON 只在 Gist 讀不到時作備援。" if source["writable"] else (
        "目前為唯讀；請在部署平台更新 POSITIONS_JSON，或設定 GH_TOKEN/GIST_ID 啟用 Gist。"
    )
    st.caption(f"持股資料來源：{source['name']}。{write_hint}")

    status = positions_store.load_status()
    if status["error"]:
        st.warning(f"{status['error']}，目前使用：{status['source']}。")
        diagnostic = status.get("diagnostic") or {}
        if diagnostic:
            detail = diagnostic.get("summary", "未提供細節")
            available_files = diagnostic.get("available_files")
            if available_files:
                detail += "；Gist 檔名：" + "、".join(available_files)
            st.caption("安全診斷：" + detail)

    if st.button("重新讀取持股", key="refresh_positions"):
        positions_store.clear_cache()
        st.rerun()

    name_by_symbol = {m.SYMBOL: m.NAME for m in levels_watch.MODS}
    holding_rows = positions_store.holdings()
    st.subheader(f"目前持股（{len(holding_rows)} 檔）")
    if holding_rows:
        overview = []
        for row in holding_rows:
            overview.append({
                "股票": name_by_symbol.get(row["symbol"], row["symbol"]),
                "代號": row["symbol"],
                "倉位": row["label"],
                "股數": row["shares"],
                "平均成本": row["cost"],
                "投入金額": round(row["shares"] * row["cost"], 2),
            })
        st.dataframe(overview, hide_index=True, use_container_width=True)
    else:
        st.info("目前沒有登記中的持股。")

    st.subheader("新增一筆買賣")
    st.write("買進會用加權平均重算成本；賣出會扣除股數，賣光後成本歸零。")
    options = {f"{m.NAME}（{m.SYMBOL}）": m for m in levels_watch.MODS}
    choice = st.selectbox("股票", list(options.keys()), key="pos_choice")
    mod = options[choice]
    symbol, name = mod.SYMBOL, mod.NAME
    label = st.text_input("倉位標籤（單一部位留 default；多倉位如 core / tactical / swing）", value="default")

    cost, shares = positions_store.get_lot(symbol, label)
    st.caption(f"目前登記：成本 {cost}　股數 {shares}")

    with st.form("trade_form"):
        action = st.radio("動作", ["buy", "sell"], horizontal=True)
        tshares = st.number_input("股數", min_value=0.0, step=1.0)
        tprice = st.number_input("價格", min_value=0.0, step=0.01)
        tdate = st.date_input("日期", value=date.today())
        note = st.text_input("備註", value="")
        submitted = st.form_submit_button("送出")
    if submitted:
        if tshares <= 0 or tprice <= 0:
            st.error("股數/價格要大於 0")
        else:
            try:
                new_cost, new_shares = positions_store.record_trade(
                    symbol, label, action, tshares, tprice, tdate.isoformat(), note, name)
                st.success(f"已更新：成本 {new_cost}　股數 {new_shares}")
                _collect.clear()
            except RuntimeError as exc:
                st.error(str(exc))

    records = positions_store.trade_history_records(symbol)
    if records:
        st.caption("這檔的交易紀錄：")
        st.table(positions_store.trade_history(symbol))
        st.caption("要取消哪一筆，就按該筆右側的「撤銷這筆」：")
        for item in reversed(records):
            action_text = "買進" if item.get("action") == "buy" else "賣出"
            col1, col2 = st.columns([5, 2])
            with col1:
                st.write(
                    f"{item.get('date', '')}｜{item.get('label', 'default')}｜"
                    f"{action_text} {item.get('shares', 0)} 股 @ {item.get('price', 0)}"
                )
            with col2:
                if st.button("撤銷這筆", key=f"undo_trade_{item['_index']}"):
                    try:
                        positions_store.undo_trade(item["_index"])
                        st.success("已撤銷指定交易，成本與股數已重新計算。")
                        _collect.clear()
                        st.rerun()
                    except (RuntimeError, ValueError) as exc:
                        st.error(str(exc))
