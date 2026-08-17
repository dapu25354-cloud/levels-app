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

import levels_watch
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
    d = _collect()
    flagged, breakout, empty, calm, errors, orders = (
        d["flagged"], d["breakout"], d["empty"], d["calm"], d["errors"], d["orders"])

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
    if st.button("查看關卡判斷"):
        with st.spinner("抓即時資料中..."):
            text = _run_module(mod)
        st.text(text)

with tab3:
    st.write("新增一筆買賣，自動用加權平均重算成本/股數（跟本機 xxx_levels.py 的邏輯一致）。")
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
            new_cost, new_shares = positions_store.record_trade(
                symbol, label, action, tshares, tprice, tdate.isoformat(), note, name)
            st.success(f"已更新：成本 {new_cost}　股數 {new_shares}")
            _collect.clear()

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
                    except ValueError as exc:
                        st.error(str(exc))
