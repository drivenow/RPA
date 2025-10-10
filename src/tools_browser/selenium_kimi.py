from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import subprocess
import time
import os
from tools_ai.text_llm import qwen_invoke
import random


# 开启调试模式
def start_chrome():
    # 打开 Chrome 浏览器，chrome.exe --remote-debugging-port=9222 --user-data-dir="E:\selenium_chrome_profile"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    user_data_dir = r"/selenium_tools/ChromeProfile"

    command = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{user_data_dir}"'

    try:

        # 使用subprocess.Popen启动Chrome浏览器

        subprocess.Popen(command, shell=True)

        print("Chrome启动成功")

    except Exception as e:

        print(f"启动Chrome时出错: {e}")


def connect_chrome():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # 使用 ChromeDriver 连接现有浏览器
    # 自动下载并使用正确版本的 ChromeDriver
    # service = Service(ChromeDriverManager().install())
    service = Service("/selenium_tools/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service,
                              options=chrome_options)
    return driver


def kimi_file_summary(driver, kimi_url, file_list):
    # 访问目标网站
    driver.get(kimi_url)  # 替换成实际的上传页面

    # 等待页面加载（可选）
    driver.implicitly_wait(10)

    for file_path in file_list:
        # 找到上传文件的 <input> 元素（替换 ID 或 XPATH）
        file_input = driver.find_element(By.XPATH, "//input[@type='file']")
        # 发送文件路径
        file_name = os.path.basename(file_path)
        file_input.send_keys(file_path)  # 替换成你要上传的文件路径

        # 可选：等待上传完成
        time.sleep(8)

        # 找到 `contenteditable="true"` 的输入框
        editor = driver.find_element(By.CSS_SELECTOR, '[contenteditable="true"]')

        # 4. 清空已有内容（如果需要）
        editor.send_keys(Keys.CONTROL + "a")  # 全选
        editor.send_keys(Keys.BACKSPACE)  # 删除已有内容

        # 5. 发送文本输入
        question = "忘掉之前的对话，总结下这篇文章的核心观点"
        new_question = qwen_invoke(question) + f":  {file_name}"
        editor.send_keys(new_question)
        # 可选：模拟 Enter 键提交
        editor.send_keys(Keys.ENTER)
        time.sleep(random.randint(70, 100))


if __name__ == '__main__':
    start_chrome()
    driver = connect_chrome()

    kimi_url = "https://kimi.moonshot.cn/chat/cu1obohdjjpkrd6v81h0"
    base_dir = r"/bili2text/outputs/比亚迪汉L 电机原理"
    file_list = os.listdir(base_dir)
    file_list = [os.path.join(base_dir, file) for file in file_list]
    print(file_list)
    kimi_file_summary(driver, kimi_url=kimi_url, file_list=file_list)
    # 关闭浏览器
    driver.quit()
