"""將未追蹤的本機持倉檔安全同步到既有私有 GitHub Gist。"""
import argparse

import positions_store


def main():
    parser = argparse.ArgumentParser(description="同步 positions_local.json 到私有 Gist")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只驗證本機檔案並顯示摘要，不呼叫 GitHub",
    )
    args = parser.parse_args()

    try:
        result = positions_store.sync_local_to_gist(dry_run=args.dry_run)
    except Exception as exc:
        print(f"同步未執行：{exc}")
        raise SystemExit(1)

    action = "驗證完成，未寫入 Gist" if result["dry_run"] else "已同步到私有 Gist"
    print(
        f"{action}：{result['symbols']} 檔、"
        f"{result['holding_lots']} 個有股數倉位、"
        f"{result['trades']} 筆交易紀錄。"
    )


if __name__ == "__main__":
    main()
