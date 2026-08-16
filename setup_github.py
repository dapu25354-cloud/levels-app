"""
setup_github.py — 一次性建立「levels-app」私有 repo 與存放持倉資料的私有 Gist。
------------------------------------------------------------
在你自己的電腦執行，Token 用 getpass 輸入(畫面不顯示、不會存檔、不會被貼進對話)：
  1. 到 https://github.com/settings/tokens/new 建一個 classic personal access token
     (fine-grained token 目前大多不支援 Gist 權限，這裡建議用 classic 的比較不會踩雷)，
     勾選兩個 scope：repo、gist，設好期限後產生，複製那串 token(只會顯示一次)。
  2. 在這個資料夾開終端機執行：python setup_github.py
  3. 執行完會印出：
       - 新建立的私有 repo 網址(等等要把這個資料夾 push 過去)
       - 新建立的私有 Gist ID(要貼進 Streamlit Cloud 的 secrets 當 GIST_ID)
"""
import getpass
import requests


def main():
    token = getpass.getpass("貼上你的 GitHub personal access token（畫面不顯示）：")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    repo_name = input("新 repo 名稱（預設 levels-app）：").strip() or "levels-app"
    r = requests.post(
        "https://api.github.com/user/repos", headers=headers,
        json={"name": repo_name, "private": True, "description": "關卡小白 Streamlit app（私有）"},
    )
    r.raise_for_status()
    repo = r.json()
    print(f"\n[OK] 私有 repo 建好了：{repo['html_url']}")

    r = requests.post(
        "https://api.github.com/gists", headers=headers,
        json={"description": "levels-app 持倉資料（私密）", "public": False,
              "files": {"positions.json": {"content": "{}"}}},
    )
    r.raise_for_status()
    gist = r.json()
    print(f"[OK] 私有 Gist 建好了，ID：{gist['id']}")

    print("\n接下來：")
    print(f"  1. git init")
    print(f"  2. git remote add origin {repo['clone_url']}")
    print(f"  3. git add . && git commit -m \"init\" && git push -u origin main")
    print(f"  4. 到 https://share.streamlit.io 用同一個 GitHub 帳號連結這個私有 repo 部署")
    print(f"  5. 部署頁的 Settings -> Secrets 貼上：")
    print(f'       APP_PW = "你自己設一個密碼"')
    print(f'       GH_TOKEN = "同一顆(或另外建一顆只有gist權限的)token"')
    print(f'       GIST_ID = "{gist["id"]}"')
    print("\n本機測試的話，把同一組值存進 .streamlit/secrets.toml（已在 .gitignore 排除，不會上傳）。")


if __name__ == "__main__":
    main()
