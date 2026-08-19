"""
positions_store.py — 私密持倉資料層
------------------------------------------------------------
真實成本/股數不寫死在各支 xxx_levels.py 裡，一律從這裡讀。

資料來源依下列優先順序自動判斷：
  1. 既有私有 GitHub Gist：設定 GH_TOKEN/GIST_ID 後，網頁永遠以 Gist 最新資料為準，
     並支援 App 原本的持倉管理寫入功能。
  2. 部署 Secret／環境變數 POSITIONS_JSON：Gist 暫時讀不到時的唯讀備援。
  3. 本機模式(預設，不用設定任何東西)：讀同資料夾的 positions_local.json；
     此檔已在 .gitignore 排除，不會被 commit、不會外流。

本機同步時，GH_TOKEN/GIST_ID 也可放在被 .gitignore 排除的
.streamlit/secrets.toml；環境變數優先於該檔案，部署端則沿用 Streamlit Secrets。

找不到資料、或 API 打不通時，一律安全降級成「空手」(cost=0, shares=0)，不會讓整份報表爆掉。
"""
import os
import json
import math
import time
import copy
import requests

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

_CACHE = None
_CACHE_TS = 0
_CACHE_TTL = 30  # 秒；同一次執行(levels_watch 跑 31 檔)只打一次 API，避免每檔各打一次
_LAST_SOURCE = None
_LAST_ERROR = None
_LOCAL_INVALID = False

FILENAME = "positions.json"
_LOCAL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positions_local.json")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCAL_SECRETS_PATH = os.path.join(_PROJECT_ROOT, ".streamlit", "secrets.toml")
POSITIONS_SECRET = "POSITIONS_JSON"


def _load_local_secrets():
    """讀取被 .gitignore 排除的本機 Streamlit Secrets，不回傳給 UI。"""
    if tomllib is None or not os.path.isfile(_LOCAL_SECRETS_PATH):
        return {}
    try:
        with open(_LOCAL_SECRETS_PATH, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _setting(name):
    """依序讀環境變數、本機 secrets.toml、部署端 Streamlit Secret。"""
    value = os.environ.get(name)
    if value:
        return value

    value = _load_local_secrets().get(name)
    if value:
        return str(value)

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


def storage_info():
    """回傳目前資料來源與是否可由 App 寫回，避免 UI 顯示敏感設定值。"""
    token, gist_id = _creds()
    if token and gist_id:
        return {"name": "私有 GitHub Gist（優先；POSITIONS_JSON 僅備援）", "writable": True}
    if _setting(POSITIONS_SECRET) is not None:
        return {"name": "部署 Secret POSITIONS_JSON（Gist 未設定）", "writable": False}
    if os.path.exists(_LOCAL_PATH):
        return {"name": "本機 positions_local.json", "writable": True}
    return {"name": "本機持倉檔（尚未建立）", "writable": True}


def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _load_local():
    return _load_local_checked(strict=False)


def _load_local_checked(strict=False):
    try:
        with open(_LOCAL_PATH, encoding="utf-8") as f:
            return _validate_data(json.load(f), "本機 positions_local.json")
    except Exception as exc:
        if strict:
            raise ValueError("本機 positions_local.json 格式錯誤，已停止同步") from exc
        return {}


def _reject_json_constant(value):
    raise ValueError(f"JSON 不接受特殊數值：{value}")


def _validate_data(data, source="持倉資料"):
    """驗證整份持倉資料；失敗時不回傳部分資料，避免半套更新。"""
    if not isinstance(data, dict):
        raise ValueError(f"{source} 必須是 JSON object")

    trade_log = data.get("_trade_log", [])
    if not isinstance(trade_log, list) or any(not isinstance(item, dict) for item in trade_log):
        raise ValueError(f"{source} 的 _trade_log 格式錯誤")

    for symbol, lots in data.items():
        if symbol == "_trade_log" or str(symbol).startswith("_"):
            continue
        if not isinstance(lots, dict):
            raise ValueError(f"{source} 的 {symbol} 倉位格式錯誤")
        for label, lot in lots.items():
            if not isinstance(lot, dict):
                raise ValueError(f"{source} 的 {symbol}/{label} 倉位格式錯誤")
            for field in ("cost", "shares"):
                if field not in lot:
                    continue
                value = float(lot[field] or 0)
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"{source} 的 {symbol}/{label}/{field} 數值錯誤")

    return data


def _load_secret(raw):
    """解析 POSITIONS_JSON，且只接受 JSON object，避免載入非預期內容。"""
    data = raw if isinstance(raw, dict) else json.loads(str(raw), parse_constant=_reject_json_constant)
    return _validate_data(data, "持倉資料")


def _save_local(data):
    _validate_data(data, "本機 positions_local.json")
    with open(_LOCAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)


def _load_gist(token, gist_id):
    r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_headers(token), timeout=10)
    r.raise_for_status()
    files = r.json().get("files", {})
    file_info = files.get(FILENAME)
    if not isinstance(file_info, dict):
        raise ValueError(f"Gist 缺少 {FILENAME}")

    content = file_info.get("content")
    if file_info.get("truncated") and file_info.get("raw_url"):
        raw = requests.get(file_info["raw_url"], headers=_headers(token), timeout=10)
        raw.raise_for_status()
        content = raw.text
    if not isinstance(content, str):
        raise ValueError(f"Gist 的 {FILENAME} 內容無效")
    return _load_secret(content)


def _load(force=False):
    global _CACHE, _CACHE_TS, _LAST_SOURCE, _LAST_ERROR, _LOCAL_INVALID
    if _CACHE is not None and not force and (time.time() - _CACHE_TS) < _CACHE_TTL:
        return _CACHE

    previous_cache = _CACHE
    _LAST_SOURCE = None
    _LAST_ERROR = None

    token, gist_id = _creds()
    if token and gist_id:
        try:
            _CACHE = _load_gist(token, gist_id)
            _LAST_SOURCE = "私有 GitHub Gist"
            _CACHE_TS = time.time()
            return _CACHE
        except Exception:
            _LAST_ERROR = "Gist 讀取或解析失敗"
            # 有已驗證過的資料時，保留它；絕不把損壞的回應合併進快取。
            if isinstance(previous_cache, dict):
                _CACHE = previous_cache
                _LAST_SOURCE = "最近一次有效的 Gist 資料"
                _CACHE_TS = time.time()
                return _CACHE

    secret_raw = _setting(POSITIONS_SECRET)
    if secret_raw is not None:
        try:
            _CACHE = _load_secret(secret_raw)
            _LAST_SOURCE = "部署 Secret POSITIONS_JSON 備援"
            _CACHE_TS = time.time()
            return _CACHE
        except Exception:
            _LAST_ERROR = "POSITIONS_JSON 解析失敗"

    try:
        _CACHE = _load_local_checked(strict=True)
        _LOCAL_INVALID = False
        _LAST_SOURCE = "本機 positions_local.json"
    except Exception:
        _LOCAL_INVALID = True
        _CACHE = {}
        if _LAST_ERROR is None:
            _LAST_ERROR = "本機 positions_local.json 讀取或解析失敗"
        _LAST_SOURCE = "空手安全狀態"
    _CACHE_TS = time.time()
    return _CACHE


def clear_cache():
    """清除記憶體快取，供使用者更新部署 Secret 後重新讀取。"""
    global _CACHE, _CACHE_TS, _LAST_SOURCE, _LAST_ERROR, _LOCAL_INVALID
    _CACHE = None
    _CACHE_TS = 0
    _LAST_SOURCE = None
    _LAST_ERROR = None
    _LOCAL_INVALID = False


def load_status():
    """回傳不含憑證的讀取狀態，供 UI/同步流程顯示。"""
    _load()
    return {"source": _LAST_SOURCE, "error": _LAST_ERROR}


def _save(data):
    global _CACHE, _CACHE_TS
    _validate_data(data, "準備寫入的持倉資料")
    token, gist_id = _creds()
    if token and gist_id:
        r = requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=_headers(token),
            json={"files": {FILENAME: {"content": json.dumps(data, ensure_ascii=False, indent=2)}}},
            timeout=10,
        )
        r.raise_for_status()
        _CACHE = copy.deepcopy(data)
        _CACHE_TS = time.time()
        return

    if _setting(POSITIONS_SECRET) is not None:
        raise RuntimeError(
            "目前只有部署 Secret POSITIONS_JSON（唯讀）。請設定 GH_TOKEN/GIST_ID，"
            "或更新部署平台的 POSITIONS_JSON，再重新整理 App。"
        )

    if not token or not gist_id:
        if _LOCAL_INVALID:
            raise RuntimeError("本機 positions_local.json 格式錯誤，已停止覆寫；請先修正檔案。")
        _save_local(data)
        _CACHE = data
        _CACHE_TS = time.time()
        return


def _summary(data):
    return {
        "symbols": sum(1 for key in data if not str(key).startswith("_")),
        "holding_lots": sum(
            1 for symbol, lots in data.items()
            if not str(symbol).startswith("_") and isinstance(lots, dict)
            for lot in lots.values()
            if isinstance(lot, dict) and float(lot.get("shares", 0) or 0) > 0
        ),
        "trades": len(data.get("_trade_log", [])),
    }


def sync_local_to_gist(dry_run=False):
    """完整驗證本機持倉後，一次同步到既有私有 Gist。"""
    # strict=True 確保本機檔損壞時不會把空資料或半套資料寫到 Gist。
    data = _load_local_checked(strict=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    summary = _summary(data)
    if dry_run:
        return {**summary, "dry_run": True}

    token, gist_id = _creds()
    if not token or not gist_id:
        raise RuntimeError("同步需要 GH_TOKEN 與 GIST_ID；請放在未追蹤的 Secrets 或環境變數中。")

    r = requests.patch(
        f"https://api.github.com/gists/{gist_id}",
        headers=_headers(token),
        json={"files": {FILENAME: {"content": payload}}},
        timeout=10,
    )
    r.raise_for_status()
    try:
        response_data = _load_gist(token, gist_id)
    except Exception as exc:
        raise RuntimeError("Gist 已送出更新，但回讀驗證失敗；請先到 Gist 確認後再重試。") from exc

    global _CACHE, _CACHE_TS, _LAST_SOURCE, _LAST_ERROR
    _CACHE = response_data
    _CACHE_TS = time.time()
    _LAST_SOURCE = "私有 GitHub Gist"
    _LAST_ERROR = None
    return {**_summary(response_data), "dry_run": False}


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
    result = record_trades([{
        "symbol": symbol, "label": label, "action": action,
        "shares": shares, "price": price, "date": date,
        "note": note, "name": name,
    }])
    return result[0]


def record_trades(trades):
    """原子地寫入多筆交易；任何一筆不合法時，不會留下半套更新。"""
    data = copy.deepcopy(_load())
    results = []
    for trade in trades:
        symbol = str(trade.get("symbol", "")).strip()
        label = str(trade.get("label", "default")).strip() or "default"
        action = trade.get("action")
        shares = float(trade.get("shares", 0) or 0)
        price = float(trade.get("price", 0) or 0)
        if not symbol:
            raise ValueError("交易缺少股票代號")
        if action not in ("buy", "sell"):
            raise ValueError(f"未知的 action: {action!r}（只接受 buy/sell）")
        if shares <= 0 or price <= 0:
            raise ValueError("交易股數與價格必須大於 0")

        lot = data.setdefault(symbol, {}).setdefault(label, {"cost": 0, "shares": 0})
        cur_cost = float(lot.get("cost", 0) or 0)
        cur_shares = float(lot.get("shares", 0) or 0)
        if action == "buy":
            new_shares = cur_shares + shares
            new_cost = (cur_cost * cur_shares + price * shares) / new_shares
        else:
            new_shares = max(0.0, cur_shares - shares)
            new_cost = cur_cost if new_shares > 0 else 0
        lot["cost"], lot["shares"] = round(new_cost, 4), new_shares
        data.setdefault("_trade_log", []).append({
            "date": trade.get("date", ""), "symbol": symbol,
            "name": trade.get("name", ""), "label": label,
            "action": action, "shares": shares, "price": price,
            "note": trade.get("note", ""),
            "before_cost": cur_cost, "before_shares": cur_shares,
        })
        results.append((round(new_cost, 4), new_shares))

    _save(data)
    return results


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


def holdings():
    """回傳目前有股數的倉位，供持股總覽使用。"""
    rows = []
    for symbol, lots in _load().items():
        if symbol.startswith("_") or not isinstance(lots, dict):
            continue
        for label, lot in lots.items():
            if not isinstance(lot, dict):
                continue
            shares = float(lot.get("shares", 0) or 0)
            if shares > 0:
                rows.append({
                    "symbol": symbol,
                    "label": label,
                    "cost": float(lot.get("cost", 0) or 0),
                    "shares": shares,
                })
    return sorted(rows, key=lambda row: (row["symbol"], row["label"]))
