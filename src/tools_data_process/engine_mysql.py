import json
import pymysql
import pandas as pd
from datetime import datetime
from tools_data_process.utils_format_text import format_text
from tools_data_process.engine_excel import ExcelEngine
from tools_data_process.utils_path import get_media_url_excel_path

# 数据库连接类
class MysqlEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)  # 首次创建实例
        return cls._instance  # 始终返回同一个实例

    def __init__(self):
        # 连接数据库
        self.db = pymysql.connect(host='192.168.1.2', port = 3306, user='admin', password='ybsDW246401.', db='mydatabase',
                                  charset='utf8')
        # 创建connection，用pandas 读取表
        self.cursor = self.db.cursor()
        self.bili_statis_df = self.__get_bili_statitics()

    def __del__(self):
        # 关闭数据库连接
        self.db.close()

    def __get_bili_statitics(self):
        try:
            poster_home_page_df = pd.read_sql("select name as poster,mid from b站个人主页", self.db).fillna('0').astype(
                {"mid": int})
            season_id_df = pd.read_sql("select `mid`, `query:season_id`, name from b站合集meta", self.db).rename(
                columns={"query:season_id": "season_id"}).fillna('0')
            season_id_df = season_id_df.astype({"mid": int, "season_id": int})
            # 合并两个表，根据mid关联
            merge_df = pd.merge(season_id_df, poster_home_page_df, on="mid", how="left")
            # print(merge_df)
            merge_df["keywords"] = merge_df["poster"] + " " + merge_df["name"]
            merge_df = merge_df[~pd.isna(merge_df["poster"])]
            return merge_df
        except:
            return pd.DataFrame()

    # 创建一个通用的数据库表，存储搜索关键词，相关网页，相关网页标题字段
    def create_common_url_table(self):
        sql = """CREATE TABLE IF NOT EXISTS `通用网页地址` (
                  `id` int(11) NOT NULL AUTO_INCREMENT,
                  `keyword` varchar(255) DEFAULT NULL,
                  `url` varchar(255) DEFAULT NULL COLLATE utf8mb4_unicode_ci,
                  `title` varchar(255) DEFAULT NULL,
                  PRIMARY KEY (`id`),
                  UNIQUE INDEX `idx_title` (`url`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1  DEFAULT CHARSET=utf8mb4;"""
        self.cursor.execute(sql)
        self.db.commit()

    # 向数据库中插入数据，入参为搜索关键词，列表中每个元素为相关网页的url和标题的元组
    def insert_common_url_data(self, keyword, url_title_pairs):
        sql = "INSERT INTO `通用网页地址` (`keyword`, `url`, `title`) VALUES (%s, %s, %s)"
        for title, url in url_title_pairs:
            try:
                self.cursor.execute(sql, (keyword, url, title))
                self.db.commit()
            except Exception as e:
                print("ERROR:", keyword, url, title, e)

    # 执行SQL语句
    def _execute_bili_vidio_sql(self, start_date=None, end_date=None):

        if start_date is None:
            start_date = '2021-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        sql = """
    select * from (
       SELECT
        DATE_FORMAT(gk_createtime, '%Y-%m-%d') AS 采集时间,
        DATE_FORMAT(pubdate, '%Y-%m-%d') AS 发布时间,
        keyword AS 搜索词,
        author AS 作者,
        title AS 标题,
        tag AS 标签,
        typename AS 视频分类,
        duration AS 时长,
        play AS 播放数,
        `like` AS 点赞量,
        favorites AS 收藏量,
        review AS 评论数量,
        danmaku AS 弹幕数量,
        video_review AS 留言量,
        description AS 视频描述,
        arcurl AS 视频地址,
        pic AS 封面,
        gk_id AS ID,
        bvid AS bvid,
        mid AS mid,
        upic AS upic,
        `desc` AS `desc`,
        url AS url,
        page AS page,
        season_id AS season_id

    FROM `b站搜索结果` )  a
    where 采集时间 >= "{}" and 采集时间 <= "{}"
    order by 播放数 desc,`发布时间` desc
    ;
        """.format(start_date, end_date)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        # 抓换为DataFrame格式
        results = pd.DataFrame(results, columns=[
            '采集时间', '发布时间', '搜索词', 'url', '作者', '标题','标签', '视频分类', '时长', '播放数', '点赞量',
            '收藏量', '评论数量', '弹幕数量', '留言量',
            '视频描述', '视频地址', '封面', 'ID', 'bvid', 'mid', 'upic', 'desc',  'page', 'season_id'        ])
        results["标题"] = results["标题"].apply(format_text)

        def get_poster(x):
            if x["搜索词"]:
                return x["搜索词"]
            else:
                if x["season_id"]:
                    try:
                        poster = self.bili_statis_df[
                            (self.bili_statis_df["season_id"] == int(x["season_id"]))]["keywords"].iloc[0]
                        # print(poster)
                    except:
                        poster = x["mid"]
                else:
                    poster = x["mid"]
                return poster

        results["搜索词"] = results.apply(lambda x: get_poster(x), axis=1)
        results["url"] = results["bvid"].apply(lambda x: "https://www.bilibili.com/video/{}".format(x) if x else None)
        search_word = results["搜索词"].unique().tolist()
        print("execute_bili_vidio_sql 搜索词：", search_word)
        result_dict = {}
        for word in search_word:
            result_dict[word] = results[results["搜索词"] == word]
        return result_dict

    def _execute_youtube_browser_sql(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = '2021-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        sql = """
        SELECT
            gk_id AS `ID`,
            DATE_FORMAT(gk_createtime, '%%Y-%%m-%%d') AS `采集时间`,
            gk_creator AS `gk_creator`,
            `playlistVideoRenderer.videoId` AS `视频ID`,
            `playlistVideoRenderer.title.runs` AS `标题JSON`,
            `playlistVideoRenderer.shortBylineText.runs` AS `作者JSON`,
            `p.V.R.Data.label` AS `视频信息`,
            `playlistVideoRenderer.videoInfo.simpleText` AS `发布时间`,
            `playlistVideoRenderer.videoInfo.runs` AS `发布时间JSON`,
            `playlistVideoRenderer.lengthText.simpleText` AS `时长`,
            `p.V.R.T.Data.label` AS `时长文本`,
            `playlistVideoRenderer.lengthSeconds` AS `时长秒`,
            `playlistVideoRenderer.navigationEndpoint.watchEndpoint.index` AS `播放列表序号`,
            `playlistVideoRenderer.thumbnail.thumbnails` AS `封面JSON`,
            `playlistVideoRenderer.thumbnailOverlays` AS `封面覆盖JSON`,
            `p.V.R.E.M.C.Metadata.url` AS `视频路径`,
            `p.V.R.E.M.C.M.P.Type` AS `页面类型`,
            `p.V.R.E.M.C.M.Ve` AS `页面Ve`,
            `p.V.R.E.E.Id` AS `端点视频ID`,
            `p.V.R.E.E.E.S.O.C.P.O.C.Config.u` AS `流媒体链接`,
            `context.client.hl` AS `语言`,
            `context.client.gl` AS `地区`,
            `context.client.remoteHost` AS `访问IP`,
            `context.client.clientName` AS `客户端名称`,
            `context.client.clientVersion` AS `客户端版本`,
            `context.client.osName` AS `操作系统`,
            `context.client.osVersion` AS `系统版本`,
            `context.client.originalUrl` AS `来源页面`,
            `context.client.mainAppWebInfo.graftUrl` AS `播放列表页面`,
            `browseId` AS `搜索词`,
            `context.client.userAgent` AS `UserAgent`
        FROM `youtube专辑列表`
        WHERE DATE(gk_createtime) >= %s AND DATE(gk_createtime) <= %s
        ORDER BY gk_createtime DESC;
        """
        self.cursor.execute(sql, (start_date, end_date))
        results = self.cursor.fetchall()
        if not results:
            print("execute_youtube_video_sql 无数据")
            return {}

        results = pd.DataFrame(results, columns=[
            'ID', '采集时间', '搜索词', '视频ID', '标题JSON', '作者JSON', '视频信息', '发布时间', '发布时间JSON',
            '时长', '时长文本', '时长秒', '播放列表序号', '封面JSON', '封面覆盖JSON', '视频路径', '页面类型',
            '页面Ve', '端点视频ID', '流媒体链接', '语言', '地区', '访问IP',
            '客户端名称', '客户端版本', '操作系统', '系统版本',
            '来源页面', '播放列表页面', '播放列表ID', 'UserAgent'
        ])

        def _parse_runs(value):
            if not value:
                return ""
            try:
                runs = json.loads(value)
                if isinstance(runs, list):
                    return "".join([item.get("text", "") for item in runs if isinstance(item, dict)])
            except Exception:
                pass
            return str(value)

        def _parse_thumbnails(value):
            if not value:
                return ""
            try:
                thumbnails = json.loads(value)
                if isinstance(thumbnails, list) and thumbnails:
                    return thumbnails[0].get("url", "")
            except Exception:
                pass
            return ""

        def _build_watch_url(path):
            if not path:
                return ""
            path = path.strip()
            if path.startswith("http"):
                return path
            return f"https://www.youtube.com{path}"

        results["标题"] = results["标题JSON"].apply(_parse_runs).apply(format_text)
        results["作者"] = results["作者JSON"].apply(_parse_runs).apply(format_text)
        results["封面"] = results["封面JSON"].apply(_parse_thumbnails)
        results["视频地址"] = results["视频路径"].apply(_build_watch_url)
        results["播放列表页面"] = results["播放列表页面"].apply(_build_watch_url)
        results["来源页面"] = results["来源页面"].apply(_build_watch_url)
        results["发布时间"] = results["发布时间"].fillna("")
        发布时间补充 = results["发布时间JSON"].apply(_parse_runs)
        results.loc[results["发布时间"] == "", "发布时间"] = 发布时间补充[results["发布时间"] == ""]
        results["视频信息"] = results["视频信息"].fillna("").apply(format_text)
        results["作者"] = results["作者"].replace("", "未知作者")
        results["播放列表序号"] = pd.to_numeric(results["播放列表序号"], errors="coerce").fillna(-1).astype(int)
        results["时长秒"] = pd.to_numeric(results["时长秒"], errors="coerce")
        results["url"] = results["视频ID"].apply(lambda x: "https://www.youtube.com/watch?v={}".format(x) if x else None)
        results.drop(columns=[
            "标题JSON", "作者JSON", "封面JSON", "封面覆盖JSON", "视频路径", "发布时间JSON"
        ], inplace=True)
        results["搜索词"] = results["作者"]
        results = results[['ID', '采集时间', '搜索词', "url", '视频ID', '标题', '作者', '视频信息', '发布时间',
                           '时长', '时长文本', '时长秒', '播放列表序号', '视频地址', '封面', '页面类型',
                           '页面Ve', '端点视频ID', '流媒体链接', '语言', '地区', '访问IP',
                           '客户端名称', '客户端版本', '操作系统', '系统版本',
                           '来源页面', '播放列表页面', '播放列表ID', 'UserAgent']]

        result_dict = {}
        for word in results["搜索词"].unique().tolist():
            result_dict[word] = results[results["搜索词"] == word].reset_index(drop=True)
        print("execute_youtube_video_sql 搜索词：", result_dict.keys())
        return result_dict

    def _execute_weixin_article_sql(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = '2021-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        sql = """
        select gk_id,    
             DATE_FORMAT(gk_createtime, '%Y-%m-%d') AS 采集时间,
            `gk_updatetime` AS `修改时间`, 
            `comm_msg_info.id` AS `消息ID`, 
            `comm_msg_info.type` AS `消息类型`, 
            `comm_msg_info.datetime` AS `消息时间`, 
            `comm_msg_info.fakeid` AS `用户假ID`, 
            `app_msg_ext_info.title` AS `文章标题`, 
            `app_msg_ext_info.digest` AS `文摘`, 
            `app_msg_ext_info.content` AS `文章内容`, 
            `app_msg_ext_info.content_url` AS `内容链接`, 
            `app_msg_ext_info.cover` AS `封面图`, 
            `app_msg_ext_info.author` AS `作者`, 
            `app_msg_ext_info.copyright_stat` AS `版权状态`,
            __biz AS `公众号ID`
        FROM `公众号主页历史文章`
            order by `消息时间` desc;
        """.format(start_date, end_date)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        # 抓换为DataFrame格式
        results = pd.DataFrame(results,
                               columns=["ID", "采集时间", "修改时间", "消息ID", "消息类型", "消息时间", "用户假ID",
                                        "文章标题", "文摘", "文章内容", "内容链接", "封面图", "作者", "版权状态",
                                        "公众号ID"])
        results["文章标题"] = results["文章标题"].apply(format_text)
        result_dict = {}
        for biz in results["公众号ID"].unique().tolist():
            result_dict[biz] = results[results["公众号ID"] == biz]
        print("execute_weixin_article_sql 公众号：", result_dict.keys())
        return result_dict

    def _execute_boss_jobs_sql(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = '2021-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        sql = """SELECT * from (
            SELECT
                gk_id AS ID,
                DATE_FORMAT(gk_createtime, '%Y-%m-%d') AS 采集时间,
                query AS 搜索词,
                bossName AS HR名字,
                bossTitle AS HR岗位,
                jobName AS 岗位名称,
                salaryDesc AS 薪资,
                skills AS 岗位要求,
                jobExperience AS 工作年限,
                brandName AS 公司名称,
                brandLogo AS 公司Logo,
                brandStageName AS 公司融资,
                brandIndustry AS 公司行业,
                brandScaleName AS 公司规模,
                welfareList AS 公司福利,
                cityName AS 岗位城市,
                areaDistrict AS 岗位区,
                businessDistrict AS 岗位街道,
                `query:city` AS 筛选地点,
                experience AS 筛选年限,
                `query:industry` AS 筛选行业,
                securityId, 
                encryptJobId,
                lid
            FROM `boss直聘职位列表` ) a
            where 采集时间 >= "{}" and 采集时间 <= "{}";
            """.format(start_date, end_date)
        print(sql)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        # 抓换为DataFrame格式
        results = pd.DataFrame(results, columns=[
            'ID', '采集时间', '搜索词', 'HR名字', 'HR岗位', '岗位名称', '薪资', '岗位要求', '工作年限', '公司名称',
            '公司Logo',
            '公司融资', '公司行业', '公司规模', '公司福利', '岗位城市', '岗位区', '岗位街道', '筛选地点', '筛选年限',
            '筛选行业',
            'securityId', 'encryptJobId', 'lid'
        ])
        print(results)
        results["岗位名称"] = results["岗位名称"].apply(format_text)
        result_dict = {}
        for query in results["搜索词"].unique().tolist():
            result_dict[query] = results[results["搜索词"] == query]
        print("excel_boss_jobs_sql 搜索词：", result_dict.keys())
        return result_dict

    def _execute_kimi_chat_sql(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = '2021-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        sql = """SELECT * from (
            SELECT 
                gk_id AS ID,
                DATE_FORMAT(gk_createtime, '%Y-%m-%d') AS 采集时间,
                DATE_FORMAT(gk_updatetime, '%Y-%m-%d') AS 修改时间,
                id AS 商品id,
                content AS 对话内容,
                context_type AS 内容类型,
                created_at AS 创建时间,
                role AS 角色,
                file_refs AS 文件连接,
                group_id AS 对话分组id,
                url_file_refs AS url_file_refs,
                url_refs AS url_refs
            FROM 
                `kimi问答`) a
            where 采集时间 >= "{}" and 采集时间 <= "{}";
            """.format(start_date, end_date)
        print(sql)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        # 抓换为DataFrame格式
        results = pd.DataFrame(results, columns=[
            'ID', '采集时间', '修改时间', '商品id', '对话内容', '内容类型', '创建时间', '角色', '文件连接',
            '对话分组id',
            'url_file_refs', 'url_refs'
        ])
        print(results)
        result_dict = {}
        for id in results["采集时间"].unique().tolist():
            result_dict[id] = results[results["采集时间"] == id]
        print("excel_kimi_chat_sql 商品id：", result_dict.keys())
        return result_dict

    # 从数据库中查询数据，入参为搜索关键词，返回列表中每个元素为相关网页的url和标题的元组
    def _execute_common_url_sql(self):
        sql = "SELECT `keyword`,`url`, `title` FROM `通用网页地址`"
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        results = pd.DataFrame(results, columns=['keyword', 'url', 'title'])
        result_dict = {}
        for keyword in results.unique().tolist():
            result_dict[keyword] = results[results["keyword"] == keyword]
        return result_dict

    def sql_to_excel(self, media_type, start_date=None, end_date=None):
        """
        不同媒体源有不同的数据结构，需要根据平台进行处理
        """
        if media_type == "bili":
            result_dict = self._execute_bili_vidio_sql(start_date=start_date, end_date=end_date)
            drop_duplicates_columns = ['标题', '视频地址']
        elif media_type == "weixin":
            result_dict = self._execute_weixin_article_sql(start_date=start_date, end_date=end_date)
            drop_duplicates_columns = ['标题']
        elif media_type == "boss":
            result_dict = self._execute_boss_jobs_sql(start_date=start_date, end_date=end_date)
            drop_duplicates_columns = ['encryptJobId']
        elif media_type == "kimi":
            result_dict = self._execute_kimi_chat_sql(start_date=start_date, end_date=end_date)
            drop_duplicates_columns = ['id']
        elif media_type == "common_url":
            result_dict = self._execute_common_url_sql()
            drop_duplicates_columns = ['网页标题']
        elif media_type == "youtube_browser":
            result_dict = self._execute_youtube_browser_sql(start_date=start_date, end_date=end_date)
            drop_duplicates_columns = ['视频ID']
        else:
            raise Exception("sql_to_excel 平台错误: {}".format(media_type))
        excel_engine1 = ExcelEngine()
        sub_file_path1, main_file_path1 = get_media_url_excel_path(media_type=media_type,
                                                                         date=datetime.now().strftime('%Y-%m-%d'))
        excel_engine1.dict_df_to_excel(result_dict, sub_file_path1)
        excel_engine1.merge_excel(sub_file_path1,
                                  main_file_path1,
                                  drop_duplicates_columns=drop_duplicates_columns)


if __name__ == '__main__':
    mysql_engine = MysqlEngine()
    # mysql_engine.create_common_url_table()
    # results = mysql_engine._execute_bili_vidio_sql()
    # results = mysql_engine._execute_weixin_article_sql()
    # print(results)
    # mysql_engine.sql_to_excel(media_type="boss", start_date="2021-01-01")
    # mysql_engine.sql_to_excel(media_type="kimi", start_date="2021-01-01")
    # mysql_engine.sql_to_excel(media_type="weixin")
    # mysql_engine.sql_to_excel(media_type="common_url")
    mysql_engine.sql_to_excel(media_type="youtube_browser")
