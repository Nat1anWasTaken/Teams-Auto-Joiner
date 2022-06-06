import datetime
import logging
import time
from threading import Thread

import requests
import schedule
import yaml
from selenium import webdriver as wd
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class DiscordColors:
    RED = 0xed4245
    GREEN = 0x57F287
    YELLOW = 0xfee75c
    BLURPLE = 0x5865f2


class BColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    def __init__(self, discord_webhook_url: str = None, notification_prefix: str = None):
        self.discord_webhook_url = discord_webhook_url
        self.notification_prefix = notification_prefix

    def success(self, message: str, title: str = None):
        print(f"{BColors.GREEN}資訊{BColors.END} {message}")
        if self.discord_webhook_url and title:
            self.send_webhook_message(title, message, DiscordColors.GREEN)

    def info(self, message: str, title: str = None):
        print(f"{BColors.BLUE}資訊{BColors.END} {message}")
        if self.discord_webhook_url and title:
            self.send_webhook_message(title, message, DiscordColors.BLURPLE)

    def warning(self, message: str, title: str = None):
        print(f"{BColors.WARNING}警告{BColors.END} {message}")
        if self.discord_webhook_url and title:
            self.send_webhook_message(title, message, DiscordColors.YELLOW)

    def error(self, message: str, title: str = None):
        print(f"{BColors.FAIL}錯誤{BColors.END} {message}")
        if self.discord_webhook_url and title:
            self.send_webhook_message(title, message, DiscordColors.RED)

    def send_webhook_message(self, title, message, color):
        requests.post(self.discord_webhook_url, json={"content": self.notification_prefix, "embeds": [
            {"color": color, "title": title, "description": message}]})


def wait_for_element_by_xpath(xpath: str, timeout: int, return_element=True, important=True):
    try:
        WebDriverWait(webdriver, timeout).until(ec.presence_of_element_located((By.XPATH, xpath)))
        if return_element:
            return webdriver.find_element(By.XPATH, xpath)
        return True
    except TimeoutException:
        if important:
            log.error("超過時間！")
        raise NoSuchElementException


def generate_webdriver():
    """
    Generate a webdriver object from webdriver config dict.
    :config: Webdriver config as dict.
    :return: A webdriver object.
    """
    option = Options()
    option.add_argument("--start-maximized")
    option.add_experimental_option("prefs", {
        "profile.cookie_controls_mode": 0,
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    })
    return wd.Edge(options=option, executable_path=config["webdriver_path"])


config = yaml.safe_load(open('config.yml', encoding='utf-8'))
webdriver = generate_webdriver()
scheduler = schedule.Scheduler()
log = Logger(discord_webhook_url=config["discord_webhook_url"], notification_prefix=config["notification_prefix"])
logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
logger.setLevel(logging.CRITICAL)


def notification(class_info: dict):
    for i in range(5):
        log.warning(f"重要課堂 {class_info['name']} [點擊前往頻道]({class_info['thread_url']})", f"重要課堂｜{class_info['name']}")
    return schedule.CancelJob


def put_tasks():
    weekdays = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday"
    }
    weekday = weekdays[datetime.datetime.now().weekday()]
    scheduler.clear()
    try:
        scheduler.every().day.at("00:00").do(put_tasks)
        for class_info in config["classes"][weekday]:
            if class_info["notification"]:
                scheduler.every().day.at(class_info["join_time"]).do(notification, class_info)
            else:
                scheduler.every().day.at(class_info["join_time"]).do(join_meet, class_info)
                scheduler.every().day.at(class_info["hangup_time"]).do(hangup_meet, class_info)
    except KeyError:
        log.error("沒有設定今天的課堂！")


def init_browser():
    webdriver.get("https://teams.microsoft.com/_#/school/")
    try:
        wait_for_element_by_xpath('//*[@id="app-bar-ef56c0de-36fc-4ef8-b417-3d82ba9d073c"]', 30, False, False)
        log.success("瀏覽器初始化完畢！看到讀取畫面是正常的", "初始化")
    except NoSuchElementException:
        log.error("初始化逾時！", "初始化")


def send_message(message, skip_check=False):
    if skip_check:
        try:
            webdriver.find_element(By.XPATH, '//button[@id="chat-button" and @track-outcome="15"]').click()
        except ElementClickInterceptedException:
            log.info("聊天介面已經打開，或是找不到聊天按鈕！")
        except NoSuchElementException:
            log.info("聊天介面已經打開，或是找不到聊天按鈕！")
    else:
        try:
            wait_for_element_by_xpath('//button[@id="chat-button" and @track-outcome="15"]',
                                      config["action_timeout"]["medium"]).click()
        except NoSuchElementException:
            log.info("聊天介面已經打開，或是找不到聊天按鈕！")
    try:
        wait_for_element_by_xpath('//div[@data-tid="ckeditor-replyConversation"]/div',
                                  config["action_timeout"]["small"]).send_keys(message)
        webdriver.find_element(By.XPATH, '//button[@id="send-message-button"]').click()
    except Exception as e:
        log.error(f"在發送訊息時出了錯誤！\n```{message}```", "錯誤")
        log.error(str(e))


def join_meet(class_info: dict):
    while True:
        webdriver.get(class_info["thread_url"])
        wait_for_element_by_xpath('//button[@id="app-bar-ef56c0de-36fc-4ef8-b417-3d82ba9d073c"]',
                                  config["action_timeout"]["large"], False)
        if not webdriver.current_url.startswith(class_info["thread_url"]):
            continue

        try:
            wait_for_element_by_xpath("//calling-join-button[1]/button[1]", config["action_timeout"]["medium"]).click()
        except NoSuchElementException:
            log.warning(f"頻道中沒有會議！將在 {config['action_timeout']['large']} 秒後重試", f"尋找會議｜{class_info['name']}")
            time.sleep(config["action_timeout"]["large"])
            continue

        found_mic = False
        while True:
            try:
                wait_for_element_by_xpath('//toggle-button[@telemetry-outcome="30"]/div/button',
                                          config["action_timeout"]["small"]).click()
                found_mic = True
            except NoSuchElementException:
                log.info("麥克風已經關閉了！")
            try:
                if found_mic:
                    webdriver.find_element(By.XPATH, '//toggle-button[@telemetry-outcome="26"]/div/button').click()
                else:
                    wait_for_element_by_xpath('//toggle-button[@telemetry-outcome="26"]/div/button',
                                              config["action_timeout"]["small"]).click()
            except NoSuchElementException:
                log.info("鏡頭已經關閉了！")
            try:
                webdriver.find_element(By.XPATH, '//toggle-button[@telemetry-outcome="29"]/div/button')
                webdriver.find_element(By.XPATH, '//toggle-button[@telemetry-outcome="25"]/div/button')
                break
            except NoSuchElementException:
                log.warning("發現到鏡頭與麥克風尚未關閉，重試中...", f"加入會議｜{class_info['name']}")
                continue

        wait_for_element_by_xpath('//button[@data-tid="prejoin-join-button"]',
                                  config["action_timeout"]["medium"]).click()

        if class_info["join_message"]:
            send_message(class_info["join_message"])
        log.success(f"成功加入會議！", f"加入會議｜{class_info['name']}")
        break
    return schedule.CancelJob


def hangup_meet(class_info: dict):
    if class_info["leave_message"]:
        send_message(class_info["leave_message"], True)
    try:
        hangup_button = webdriver.find_element(By.XPATH, '//button[@id="hangup-button"]')
        ActionChains(webdriver).move_to_element(hangup_button).click().perform()
    except NoSuchElementException:
        log.warning("沒有找到掛斷按鈕！會議可能已經掛斷", f"掛斷會議｜{class_info['name']}")
        return schedule.CancelJob
    except AttributeError:
        log.warning("沒有找到掛斷按鈕！會議可能已經掛斷", f"掛斷會議｜{class_info['name']}")
        return schedule.CancelJob
    try:
        wait_for_element_by_xpath('//span[ @ translate - once = "calling_cqf_button_cancel"]',
                                  config["action_timeout"]["small"], True, False).click()
    except AttributeError:
        pass
    except NoSuchElementException:
        pass
    log.info("已掛斷會議！", f"離開會議｜{class_info['name']}")
    return schedule.CancelJob


def main():
    thread = Thread(target=init_browser)
    thread.start()
    scheduler.every().day.at("00:00").do(put_tasks)
    put_tasks()
    while True:
        scheduler.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
