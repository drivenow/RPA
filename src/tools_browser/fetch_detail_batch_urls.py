from curl_cffi import requests
from xml.etree import ElementTree
import pandas as pd
import os
from src.tools_data_process.engine_mysql import MysqlEngine
from src.tools_data_process.utils_path import get_root_media_save_path

batch_urls_base_dir = get_root_media_save_path("homepage_url", None)[1]


def __get_url_gkdata():
    df = pd.read_excel(os.path.join(batch_urls_base_dir, "www_yuque_api_docs_json_data_20250309091052.xlsx"))
    url_pairs = []
    url_dict = {}
    url_dict["title"] = df["标题"].values.tolist()
    url_dict["url"] = ["https://www.yuque.com/gk.ai/gkdata/" + i for i in df["slug"].values.tolist()]
    for i in range(len(url_dict["url"])):
        url_pairs.append((url_dict["title"][i], url_dict["url"][i]))
    return url_dict


def __get_url_weixin(topic_keyword):
    mysql_engine = MysqlEngine()
    result_dict = mysql_engine._execute_weixin_article_sql()
    homepage_dict = pd.read_excel(os.path.join(batch_urls_base_dir, r"home_page_url.xlsx"))[
        ["主页名称", "__biz"]].set_index("主页名称").T.to_dict()
    print(homepage_dict)
    result_df = result_dict[homepage_dict[topic_keyword]["__biz"]]
    # debug 
    # result_df = result_df[result_df["文章标题"]=="买卖压力度量，复权调整成交量之后，效果居然能有提升！"]
    url_dict = {}
    url_dict["title"] = result_df["文章标题"].values.tolist()
    url_dict["url"] = result_df["内容链接"].values.tolist()
    return url_dict


def get_batch_urls(sitemap_url="https://ai.pydantic.dev/sitemap.xml", save_to_db=False):
    """
    Fetches all URLs from the Pydantic AI documentation.
    Uses the sitemap (https://ai.pydantic.dev/sitemap.xml) to get these URLs.

    Returns:
        List[str]: List of URLs
    """
    if sitemap_url.lower() == "gkdata":
        keywords = "gkdata"
        url_pairs = __get_url_gkdata()
        if save_to_db:
            mysql_engine = MysqlEngine()
            mysql_engine.insert_common_url_data(keywords, url_pairs)
        return url_pairs["url"], url_pairs["title"], keywords
    elif sitemap_url.startswith("weixin"):
        keywords = sitemap_url.split("_")[-1]
        url_pairs = __get_url_weixin(keywords)
        if save_to_db:
            mysql_engine = MysqlEngine()
            mysql_engine.insert_common_url_data(keywords, url_pairs)
        return url_pairs["url"], url_pairs["title"], keywords
    else:
        try:
            # 获取sitemapurl中的域名
            keywords = sitemap_url.replace("https://", "").replace("http://", "").split("/")[0]
            print(keywords)
            response = requests.get(sitemap_url)
            response.raise_for_status()

            # Parse the XML
            root = ElementTree.fromstring(response.content)

            # Extract all URLs from the sitemap
            # The namespace is usually defined in the root element
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            url_pairs = []
            urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
            urls = [url + "/" if not url.endswith("/") else url for url in urls]
            url_dict = {"title": [url[url.find(keywords) + len(keywords) + 1:] for url in urls], "url": urls}
            url_dict["title"] = ["homepage" if title == "" else title for title in url_dict["title"]]
            for i in range(len(url_dict["url"])):
                url_pairs.append((url_dict["title"][i], url_dict["url"][i]))
            if save_to_db:
                mysql_engine = MysqlEngine()
                mysql_engine.insert_common_url_data(keywords, url_pairs)
            return url_dict["url"], url_dict["title"], keywords
        except Exception as e:
            print(f"Error fetching sitemap: {e}")
            return [], [], keywords


if __name__ == '__main__':
    # batch_urls, batch_titles, keywords = get_batch_urls(sitemap_url="https://ai.pydantic.dev/sitemap.xml")
    # batch_urls, batch_titles, keywords = get_batch_urls(sitemap_url="https://docs.crawl4ai.com/sitemap.xml")
    # print(len(batch_urls))
    # batch_urls, batch_titles, keywords = get_batch_urls(sitemap_url="gkdata")
    weixin_df = pd.read_excel(os.path.join(batch_urls_base_dir, r"home_page_url.xlsx"))
    for homepage_name in weixin_df["主页名称"]:
        batch_urls, batch_titles, keywords = get_batch_urls(sitemap_url=f"weixin_{homepage_name}")
        print(batch_urls)
