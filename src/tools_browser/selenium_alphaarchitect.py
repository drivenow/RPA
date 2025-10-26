import time
from typing import Iterable, List, Set, Tuple

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 可根据实际环境调整 WebDriver 路径
CHROMEDRIVER_PATH = r"/selenium_tools/chromedriver-win64/chromedriver.exe"

# 收集的文件类型
FILE_SUFFIXES: Tuple[str, ...] = (".pdf", ".xlsx", ".xls", ".csv", ".doc", ".docx", ".ppt", ".pptx")


def make_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


def _collect_file_links(driver: webdriver.Chrome) -> Set[str]:
    links: Set[str] = set()
    for anchor in driver.find_elements(By.TAG_NAME, "a"):
        href = anchor.get_attribute("href")
        if not href:
            continue
        lower_href = href.lower()
        if lower_href.endswith(FILE_SUFFIXES):
            links.add(href)
    return links


def _click_load_more(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    selectors: Iterable[Tuple[By, str]] = (
        (By.CSS_SELECTOR, "a.load_more_posts"),
        (By.CSS_SELECTOR, "button.load_more_posts"),
        (By.CSS_SELECTOR, "#load_more_posts"),
        (By.CSS_SELECTOR, ".load-more-posts a"),
        (By.CSS_SELECTOR, ".load-more-posts button"),
    )
    for by, selector in selectors:
        try:
            button = wait.until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", button)
            return True
        except TimeoutException:
            continue
    return False


def scrape_research_files(
    target_url: str = "https://alphaarchitect.com/research-category-list/",
    *,
    wait_seconds: int = 15,
    pause_seconds: float = 2.0,
) -> List[str]:
    driver = make_driver()
    wait = WebDriverWait(driver, wait_seconds)
    file_links: Set[str] = set()
    try:
        driver.get(target_url)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article")))

        while True:
            file_links.update(_collect_file_links(driver))
            current_posts = len(driver.find_elements(By.CSS_SELECTOR, "article"))
            clicked = _click_load_more(driver, wait)
            if not clicked:
                break
            try:
                wait.until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "article")) > current_posts
                )
            except TimeoutException:
                break
            time.sleep(pause_seconds)
        final_links = sorted(file_links)
        return final_links
    finally:
        driver.quit()


if __name__ == "__main__":
    links = scrape_research_files()
    print(f"共找到 {len(links)} 个文件链接:")
    for url in links:
        print(url)
