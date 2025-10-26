from curl_cffi import requests
import parsel
from pprint import pprint
from bs4 import BeautifulSoup


# CSS选择器
def parse_css_pattern(content, css_pattern):
    # 使用parsel解析
    selector = parsel.Selector(text=content)
    titles_css = selector.css(css_pattern).getall()
    print("\nCSS选择器结果:")
    if titles_css:
        for i, title in enumerate(titles_css, 1):
            print(f"{i}. {title.strip()}")
    else:
        print("CSS选择器没有找到结果")
    return titles_css


# XPath选择器
def parse_xpath_pattern(content, xpath_pattern_list):
    # 使用parsel解析
    selector = parsel.Selector(text=content)
    for xpath_pattern in xpath_pattern_list:
        titles_xpath = selector.xpath(xpath_pattern).getall()
        print("\nXPath选择器结果:")
        if titles_xpath:
            for i, title in enumerate(titles_xpath, 1):
                print(f"{i}. {title.strip()}")
            return titles_xpath
        else:
            print("XPath选择器没有找到结果")


def parse_bili_search_result(content):
    # 解析B站搜索结果页面
    title_pattern_list = [
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[*]/div/div[2]/div/div/a/h3[@title]/@title',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[3]/div/div[*]/div/div[2]/div/div/a/h3[@title]/@title',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div[1]/div[*]/div/div[2]/div/div/a/h3[@title]/@title'
    ]
    brodcast_pattern_list = [
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div[1]/div[*]/div/div[2]/div/div/div/a/span[1][@class="bili-video-card__info--author"]/text()',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[*]/div/div[2]/div/div/div/a/span[1][@class="bili-video-card__info--author"]/text()', ]

    url_pattern_list = ['//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[*]/div/div[2]/a/@href',
                        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[3]/div/div[*]/div/div[2]/a/@href',
                        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div[1]/div[*]/div/div[2]/a/@href',
                        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div[1]/div[*]/div/div[2]/a/@href',
                        # '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div[1]/div[4]/div/div[2]/a/@href'
                        ]
    # 播放量
    play_pattern_list = [
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div[1]/div[*]/div/div[2]/a/div/div[2]/div/div/span[1]/span[1][@data-v-74991839]/text()',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[3]/div/div[*]/div/div[2]/a/div/div[2]/div/div/span[1]/span[1][@data-v-74991839]/text()',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[*]/div/div[2]/a/div/div[2]/div/div/span[1]/span[1][@data-v-74991839]/text()',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[*]/div/div[2]/a/div/div[2]/div/div/span/span[1][@data-v-74991839]/text()',
        '//*[@id="i_cecream"]/div/div[2]/div[2]/div/div/div/div[2]/div/div[*]/div/div[2]/a/div/div[2]/div/div/span[1]/span[@data-v-74991839]/text()',
    ]
    title_list = parse_xpath_pattern(content, title_pattern_list)
    author_list = parse_xpath_pattern(content, brodcast_pattern_list)
    url_list = parse_xpath_pattern(content, url_pattern_list)
    url_list = ['https:' + url if url.startswith('//') else url for url in url_list]
    play_list = parse_xpath_pattern(content, play_pattern_list)
    new_play_list = []
    ii = 0
    for i in range(len(url_list)):
        if url_list[i].startswith('https://cm.bilibili.com/cm/api/fees/pc/sync'):
            new_play_list.append(0)
        else:
            new_play_list.append(play_list[ii])
            ii += 1

    result = {}
    result['标题'] = title_list
    result['播放数'] = new_play_list
    result['作者'] = author_list
    result['链接'] = url_list
    pprint(result)
    return result


def parse_boss_zhipin_search_result(content):
    # 定义所有需要提取的XPath表达式
    xpaths = {
        # 职位基本信息
        'job_title': ['.//span[@class="job-name"]/text()',
                      '//*[@id="wrap"]/div[2]/div[2]/div/div[1]/div[1]/ul/li[12]/div[1]/a/div[1]/span[1]'],
        # [@class="job-name"]/text()
        'job_area': './/span[@class="job-area"]/text()',
        'salary': './/span[@class="salary"]/text()',

        # 职位要求
        'requirements': './/ul[@class="tag-list"]/li/text()',

        # 招聘者信息
        'recruiter': './/div[@class="info-public"]/text()',
        'recruiter_title': './/div[@class="info-public"]/em/text()',

        # 公司信息
        'company_name': './/h3[@class="company-name"]/a/text()',
        'company_tags': './/ul[@class="company-tag-list"]/li/text()',

        # 职位标签
        'job_tags': './/div[@class="job-card-footer"]//ul[@class="tag-list"]/li/text()',

        # 链接信息
        'job_link': './/a[contains(@class, "job-card-left")]/@href',
        'company_link': './/h3[@class="company-name"]/a/@href',
        'company_logo': './/div[@class="company-logo"]//img/@src'
    }

    # 解析结果
    result = {}

    # 遍历所有XPath表达式并提取数据
    for msg_key, xpath_list in xpaths.items():
        if isinstance(xpath_list, str):
            xpath_list = [xpath_list]
        elements = parse_xpath_pattern(content, xpath_list)
        if elements:
            print(f"{msg_key}: {elements[0]}")
        else:
            print(f"{msg_key}: 未找到")
        # # 处理列表类型的数据
        # if msg_key in ['requirements', 'company_tags', 'job_tags']:
        #     result[msg_key] = [item.strip() for item in elements if item.strip()]
        # else:
        #     # 处理单个值
        #     result[msg_key] = elements[0].strip() if elements else ''

    return result


def parse_weixin_article(content):
    xpaths = {
        # 文章作者
        'author': ['//*[@id="js_author_name"]//text()'],
        # 文章标题
        'title': ['//*[@id="activity-name"]//text()'],
        # 文章内容
        'content': ['//*[@id="js_content"]/p[*]//text()'],
    }

    # 解析结果
    result = {}

    # 遍历所有XPath表达式并提取数据
    for msg_key, xpath_list in xpaths.items():
        if isinstance(xpath_list, str):
            xpath_list = [xpath_list]
        elements = parse_xpath_pattern(content, xpath_list)
        elements = "\n".join(elements).strip()
        if elements:
            result[msg_key] = elements
            print(f"{msg_key}: {elements[0]}")
        else:
            result[msg_key] = []
            print(f"{msg_key}: 未找到")
    return result


########################################
if __name__ == '__main__':
    url = 'https://search.bilibili.com/all?keyword={}&from_source=banner_search'.format("南京")
    url = 'https://www.zhipin.com/web/geek/job?query={}&city=101190100&experience=104,105&scale=306&jobType=1901&salary=407'.format(
        "文档工程师")
    url = "https://mp.weixin.qq.com/s?__biz=MzUyMzUyNzM4Ng==&mid=2247504247&idx=2&sn=41bdfc75f19e70ac168362e510ea7b3b&chksm=fa39a4c2cd4e2dd459a6ae4afb90a404f5dc77a0012be79206eb09394b51eb8557725ab254df&scene=127#wechat_redirect"

    print("请求地址:", url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    response = requests.get(url, headers=headers, impersonate="chrome120")
    content = response.text
    # content = open('page.html', 'r', encoding='utf-8').read()  # 读取本地文件内容，用于调试
    print(content)
    if response.status_code == 200:
        # result = parse_bili_search_result(content)
        # result = parse_boss_zhipin_search_result(content)
        result = parse_weixin_article(content)
    else:
        print("请求失败")

    # 打印页面内容片段，用于调试
    print("\n页面内容片段:", result)
    with open('page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    # print(response.text)  # 打印前500个字符

    # 保存结果到Excel文件
    # from src.tools_data_process.to_excel import dict_to_excel
    # write_path = '../data/bili_search_result.xlsx'
    # dict_to_excel(result, write_path)
