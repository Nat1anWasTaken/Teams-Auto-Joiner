# Teams Auto Joiner

在上課時間自動加入Teams會議，因為只是個小腳本，代碼品質屬於能用就好，別太講究#

## 前置軟體/套件

* Python >= 3.10
* pip >= 21.3.1
* Microsoft Edge
* [Microsoft Edge WebDriver](https://developer.microsoft.com/zh-tw/microsoft-edge/tools/webdriver/) == Microsoft Edge 版本

## 快速開始

1. 把這個專案`clone`下來並`cd`進去

```powershell
git clone https://github.com/NathanTW0219/Teams-Auto-Joiner.git
```

```powershell
cd Teams-Auto-Joiner
```

2. 將 `config.example.yml` 重新命名成 `config.yml` 並填入其中欄位

```yaml
webdriver_path: "C:/msedgedriver.exe"  # Webdriver 的位置

classes:
  saturday: # 週六的課堂資訊
    - name: "Example Class"
      join_time: "00:00"
      leave_time: "00:01"
      thread_url: "https://teams.microsoft.com/_#/school/conversations/..."
      join_message: "Join Message"
      leave_message: "Leave Message"
      notification: false

retry_latency: 60  # 發現頻道沒有會議後的等待時間

action_timeout: # 執行動作的時間限制
  large: 30
  medium: 10
  small: 2

discord_webhook_url: "https://discord.com/api/webhooks/..."  # 用於通知的 Discord Webhook URL
notification_prefix: "<@...>"  # 通知的標題前綴，通常用於@mention用戶
```

3. 安裝專案所需的Python模組

```powershell
pip install -r requirements.txt
```

4. 運行他

```powershell
python main.py
```