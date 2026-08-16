"""
positions_store.py — 私密持倉資料層
------------------------------------------------------------
真實成本/股數不寫死在各支 xxx_levels.py 裡，一律從這裡讀。

兩種儲存模式，自動判斷用哪一種：
  1. 本機模式(預設，不用設定任何東西)：存在同資料夾一個 positions_local.json，
     已在 .gitignore 排除，不會被 commit、不會外流。這是給「在自己電腦跑、
     手機連同一個 WiFi 打開」這種最簡單用法的。
  2. 雲端模式(選用，之後想部署到 Streamlit Cloud 才需要)：設定 GH_TOKEN/GIST_ID
     後，改存在一個私有 GitHub Gist，本機從環境變數讀，雲端從 st.secrets 讀。
     即使這個 repo(程式碼/判斷規則)意外外洩，也不會連帶洩漏真實金額。

找不到資料、或 API 打不通時，一律安全降級成「空手」(cost=0, shares=0)，不會讓整份報表爆掉。
"""
import os
import json
import time
import requests

_CACHE = None
_CACHE_TS = 0
_CACHE_TTL = 30  # 秒；同一次執行(levels_watch 跑 31 檔)只打一次 API，避免每檔各打一次

FILENAME = "positions.json"
_LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positions_local.json")


def _creds():
    token = os.environ.get("GH_TOKEN")
    gist_id = os.environ.get("GIST_ID")
    if not token or not gist_id:
        try:
            import streamlit as st
            token = token or st.secrets.get("GH_TOKEN")
            gist_id = gist_id or st.secrets.get("GIST_ID")
        except Exception:
            pass
    return token, gist_id


def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _load_local():
    try:
        with open(_LOCAL_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_local(data):
    with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load(force=False):
    global _CACHE, _CACHE_TS
    if _CACHE is not None and not force and (time.time() - _CACHE_TS) < _CACHE_TTL:
        return _CACHE
    token, gist_id = _creds()
    if not token or not gist_id:
        _CACHE = _load_local()
        _CACHE_TS = time.time()
        return _CACHE
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_headers(token), timeout=10)
        r.raise_for_status()
        content = r.json()["files"][FILENAME]["content"]
        _CACHE = json.loads(content)
    except Exception:
        _CACHE = _CACHE or {}
    _CACHE_TS = time.time()
    return _CACHE


def _save(data):
    global _CACHE, _CACHE_TS
    token, gist_id = _creds()
    if not token or not gist_id:
        _save_local(data)
        _CACHE = data
        _CACHE_TS = time.time()
        return
    r = requests.patch(
        f"https://api.github.com/gists/{gist_id}",
        headers=_headers(token),
        json={"files": {FILENAME: {"content": json.dumps(data, ensure_ascii=False, indent=2)}}},
        timeout=10,
    )
    r.raise_for_status()
    _CACHE = data
    _CACHE_TS = time.time()


def get_lot(symbol, label="default"):
    """回傳 (cost, shares)；沒登記過就是 (0, 0) = 空手。"""
    lot = _load().get(symbol, {}).get(label, {})
    return float(lot.get("cost", 0) or 0), float(lot.get("shares", 0) or 0)


def get_lot_full(symbol, label="default"):
    """回傳整包 dict(含 entry_date/last_exit/fully_added 等額外欄位)。"""
    return dict(_load().get(symbol, {}).get(label, {}))


def set_lot(symbol, label, cost, shares, **extra):
    """直接覆寫一組倉位(app 的持倉編輯表單用這個)。"""
    data = _load()
    data.setdefault(symbol, {})[label] = {"cost": round(float(cost), 4), "shares": float(shares), **extra}
    _save(data)


def record_trade(symbol, label, action, shares, price, date, note="", name=""):
    """買/賣一筆：買進用加權平均重算成本，賣出扣減股數(賣光成本歸零)，
    同時把這筆紀錄進交易歷史(欄位比照本機 trade_log.json)。"""
    data = _load()
    lot = data.setdefault(symbol, {}).setdefault(label, {"cost": 0, "shares": 0})
    cur_cost, cur_shares = float(lot.get("cost", 0) or 0), float(lot.get("shares", 0) or 0)
    if action == "buy":
        new_shares = cur_shares + shares
        new_cost = (cur_cost * cur_shares + price * shares) / new_shares if new_shares else 0
    elif action == "sell":
        new_shares = max(0.0, cur_shares - shares)
        new_cost = cur_cost if new_shares > 0 else 0
    else:
        raise ValueError(f"未知的 action: {action!r}（只接受 buy/sell）")
    lot["cost"], lot["shares"] = round(new_cost, 4), new_shares
    history = data.setdefault("_trade_log", [])
    history.append({
        "date": date, "symbol": symbol, "name": name, "label": label,
        "action": action, "shares": shares, "price": price, "note": note,
    })
    _save(data)
    return new_cost, new_shares


def trade_history(symbol=None):
    hist = _load().get("_trade_log", [])
    return [h for h in hist if symbol is None or h["symbol"] == symbol]


def all_symbols():
    return [s for s in _load().keys() if not s.startswith("_")]
