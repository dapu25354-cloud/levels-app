"""
positions_store.py — 私密持倉資料層
------------------------------------------------------------
真實成本/股數不寫死在各支 xxx_levels.py 裡，一律從這裡讀。

資料來源依下列優先順序自動判斷：
  1. 部署 Secret／環境變數 POSITIONS_JSON：直接放持倉 JSON，適合 Streamlit Cloud。
     這個來源是唯讀的；要修改內容時，請更新部署平台的 Secret。
  2. 既有私有 GitHub Gist：設定 GH_TOKEN/GIST_ID 後使用，保留舊部署方式相容性，
     並支援 App 原本的持倉管理寫入功能。
  3. 本機模式(預設，不用設定任何東西)：讀同資料夾的 positions_local.json；
     此檔已在 .gitignore 排除，不會被 commit、不會外流。

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
POSITIONS_SECRET = "POSITIONS_JSON"


def _setting(name):
    """讀取環境變數或 Streamlit Secret；空字串視為未設定。"""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return None


def _creds():
    return _setting("GH_TOKEN"), _setting("GIST_ID")


def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _load_local():
    try:
        with open(_LOCAL_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_secret(raw):
    """解析 POSITIONS_JSON，且只接受 JSON object，避免載入非預期內容。"""
    data = raw if isinstance(raw, dict) else json.loads(str(raw))
    if not isinstance(data, dict):
        raise ValueError("POSITIONS_JSON 必須是 JSON object")
    return data


def _save_local(data):
    with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load(force=False):
    global _CACHE, _CACHE_TS
    if _CACHE is not None and not force and (time.time() - _CACHE_TS) < _CACHE_TTL:
        return _CACHE
    secret_raw = _setting(POSITIONS_SECRET)
    if secret_raw is not None:
        try:
            _CACHE = _load_secret(secret_raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            # Secret 已設定但格式錯誤時不可退回本機檔，避免部署環境誤顯示本機持倉。
            _CACHE = {}
        _CACHE_TS = time.time()
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
    if _setting(POSITIONS_SECRET) is not None:
        raise RuntimeError(
            "目前使用部署 Secret POSITIONS_JSON（唯讀）。請更新部署平台的 Secret，"
            "再重新整理 App。"
        )
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
        "before_cost": cur_cost, "before_shares": cur_shares,
    })
    _save(data)
    return new_cost, new_shares


def undo_last_trade(symbol, label="default"):
    """撤銷指定股票/倉別最後一筆交易，並恢復交易前的成本與股數。"""
    data = _load()
    history = data.get("_trade_log", [])
    target_index = None
    for index in range(len(history) - 1, -1, -1):
        item = history[index]
        if item.get("symbol") == symbol and item.get("label", "default") == label:
            target_index = index
            break
    if target_index is None:
        return None

    item = history[target_index]
    lot = data.setdefault(symbol, {}).setdefault(label, {"cost": 0, "shares": 0})

    # 新紀錄會保存交易前狀態，撤銷時可精準恢復；舊紀錄則使用反向計算相容處理。
    if "before_cost" in item and "before_shares" in item:
        lot["cost"] = round(float(item["before_cost"] or 0), 4)
        lot["shares"] = float(item["before_shares"] or 0)
    else:
        current_cost = float(lot.get("cost", 0) or 0)
        current_shares = float(lot.get("shares", 0) or 0)
        trade_shares = float(item.get("shares", 0) or 0)
        trade_price = float(item.get("price", 0) or 0)
        if item.get("action") == "buy":
            previous_shares = current_shares - trade_shares
            if previous_shares < -1e-9:
                raise ValueError("目前持股資料與交易紀錄不一致，無法安全撤銷")
            lot["shares"] = max(0.0, previous_shares)
            lot["cost"] = round(
                max(0.0, (current_cost * current_shares - trade_price * trade_shares)
                    / previous_shares) if previous_shares > 1e-9 else 0.0,
                4,
            )
        elif item.get("action") == "sell":
            lot["shares"] = current_shares + trade_shares
        else:
            raise ValueError("未知的交易類型，無法撤銷")

    history.pop(target_index)
    _save(data)
    return item


def _apply_trade_state(cost, shares, item):
    trade_shares = float(item.get("shares", 0) or 0)
    trade_price = float(item.get("price", 0) or 0)
    if item.get("action") == "buy":
        new_shares = shares + trade_shares
        new_cost = ((cost * shares) + (trade_price * trade_shares)) / new_shares if new_shares else 0
        return new_cost, new_shares
    if item.get("action") == "sell":
        new_shares = max(0.0, shares - trade_shares)
        return (cost if new_shares > 0 else 0.0), new_shares
    raise ValueError("未知的交易類型，無法撤銷")


def _reverse_trade_state(cost, shares, item):
    trade_shares = float(item.get("shares", 0) or 0)
    trade_price = float(item.get("price", 0) or 0)
    if item.get("action") == "buy":
        previous_shares = shares - trade_shares
        if previous_shares < -1e-9:
            raise ValueError("目前持股資料與交易紀錄不一致，無法安全撤銷")
        previous_cost = (
            (cost * shares - trade_price * trade_shares) / previous_shares
            if previous_shares > 1e-9 else 0.0
        )
        return max(0.0, previous_cost), max(0.0, previous_shares)
    if item.get("action") == "sell":
        # 若舊紀錄剛好賣光，舊格式沒有保存賣出前成本，只能保留現有可知成本。
        return cost, shares + trade_shares
    raise ValueError("未知的交易類型，無法撤銷")


def undo_trade(trade_index):
    """撤銷交易歷史中的指定一筆，並重算該股票/倉別後續交易。"""
    data = _load()
    history = data.get("_trade_log", [])
    if not isinstance(trade_index, int) or not 0 <= trade_index < len(history):
        return None

    target = history[trade_index]
    symbol = target.get("symbol")
    label = target.get("label", "default")
    lot = data.setdefault(symbol, {}).setdefault(label, {"cost": 0, "shares": 0})
    stream = [
        item for item in history
        if item.get("symbol") == symbol and item.get("label", "default") == label
    ]

    target_before = (target.get("before_cost"), target.get("before_shares"))
    if target_before[0] is not None and target_before[1] is not None:
        # 新格式保存了目標交易前狀態，因此只需從那個狀態重播後續交易。
        cost, shares = float(target_before[0] or 0), float(target_before[1] or 0)
        replay = stream[stream.index(target) + 1:]
    else:
        # 舊格式沒有快照，先由目前持股反向推回最早紀錄，再跳過目標交易重播。
        cost, shares = float(lot.get("cost", 0) or 0), float(lot.get("shares", 0) or 0)
        for item in reversed(stream):
            cost, shares = _reverse_trade_state(cost, shares, item)
        replay = [item for item in stream if item is not target]

    for item in replay:
        cost, shares = _apply_trade_state(cost, shares, item)

    lot["cost"], lot["shares"] = round(cost, 4), shares
    history.pop(trade_index)
    _save(data)
    return target


def trade_history_records(symbol=None):
    """回傳交易紀錄及其在原始歷史中的索引，供介面逐筆撤銷。"""
    hist = _load().get("_trade_log", [])
    fields = ("date", "symbol", "name", "label", "action", "shares", "price", "note")
    return [
        {**{field: h.get(field, "") for field in fields}, "_index": index}
        for index, h in enumerate(hist)
        if symbol is None or h.get("symbol") == symbol
    ]


def trade_history(symbol=None):
    return [{key: value for key, value in item.items() if key != "_index"}
            for item in trade_history_records(symbol)]


def all_symbols():
    return [s for s in _load().keys() if not s.startswith("_")]
