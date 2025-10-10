from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import List
from model_utils import model


class SourceSQLSchema(BaseModel):
    """数据模型描述容器

    Attributes:
        schema: 数据库字段名称
        example: 字段值的典型示例

    Examples:
        >>> SourceSQLSchema( field_names=\"age \\n name\", field_examples="18-25岁, tom")
    """

    field_names: str = Field(
        description="数据库字段名称，同时包含多个字段，每一行为一个字段",
        examples="age \n name",
        maxLength=10000,
    )

    field_examples: str = Field(
        description="字段值的典型示例，对应schema中的每个字段输出的示例值",
        example="18-25岁, tom",
        max_length=10000
    )


class SimpleSQLSchema(BaseModel):
    """
    返回简化后的数据模型描述容器
    Attributes:
        field_comments: 简化后的数据库字段名称，包含名称和注释
    """
    field_comments: List[str] = Field(
        [],
        description="数据库字段名称和注释，同时包含多个字段",
        examples=[["age：年龄", "name：姓名"]],
        title="字段Schema定义名称"
    )


simplify_agent = Agent(
    model=model,
    result_type=SimpleSQLSchema,
    system_prompt=(
        "你需要仔细提供阅读数据库字段信息和字段内容，按要求完成数据处理。"
    ),
)


@simplify_agent.tool
def annotation_fields_by_input(ctx: RunContext[str]) -> SimpleSQLSchema:
    """根据输入的数据库字段信息，简化字段名称和注释"""
    # print(ctx.deps.dict())
    # print(ctx.prompt)
    # return "Prompt: " + ctx.prompt + str(ctx.deps.dict())
    try:
        prompt = ctx.prompt + str(ctx.deps.model_dump())
        print("Prompt: " + prompt)
    except:
        prompt = ctx.prompt
    return prompt


if __name__ == '__main__':
    oneline_feilds = """
https://www.coze.cn/store/agent/7340211457092583465?bid=6ek0nl8hg9g09&from=bots_card&panel=1&post_id=7414699438729461811
请帮忙注释数据表“api-public_lingowhale_feed_subscription_json_data.feed_list”如下字段，不要改变格式，注释内容精简，如遇到字段包含.的，取右边字符串。
entry_id：
entry_type：
feed_source：
title：
url：
category：
pub_time：
surface_url：
info_source.info_source_type：
info_source.info_source_id：
info_source.info_source_name：
info_source.info_source_profile：
info_source.info_source_profile_name：
info_source.last_update_time：
info_source.info_source_root：
info_source.info_source_description：
info_source.info_source_category：
info_source.rec_rank：
info_source.default_select：
info_source.can_cancel：
info_source.shield：
info_source.is_ban：
has_read：
description：
is_hot：
content_length：
read_progress：
recommend_source：
theme_color：
novel_form_surface_url：
channel.channel_id：
channel.name：
channel.info_sources：
channel.description：
channel.surface_url：
channel.status：
channel.creator_id：
channel.has_subscribed：
cursor：
sort_type：
limit：
filter_unread：
channel_ids：
    """
    online_examples = """
entry_id	entry_type	feed_source	title	url	category	pub_time	surface_url	info_source.info_source_type	info_source.info_source_id	info_source.info_source_name	info_source.info_source_profile	info_source.info_source_profile_name	info_source.last_update_time	info_source.info_source_root	info_source.info_source_description	info_source.info_source_category	info_source.rec_rank	info_source.default_select	info_source.can_cancel	info_source.shield	info_source.is_ban	has_read	description	is_hot	content_length	read_progress	recommend_source	theme_color	novel_form_surface_url	channel.channel_id	channel.name	channel.info_sources	channel.description	channel.surface_url	channel.status	channel.creator_id	channel.has_subscribed	cursor	sort_type	limit	filter_unread	channel_ids
68120ef053c14ecb7886de11	7	9	期货交易可能出现的七次大坑，掉进去不容易出来？			2025-04-30 18:02:08	https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/resource_server/20250430195404_1917547999404183552_786242.png	2	67748456eee9135b1ce60f36	翌派量化	https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/2atSWN4rfbhT1EGiq640PtfP.jpeg	翌派量化	2025-04-30 19:52:16	mp.weixin.qq.com	可视化量化、策略分享、最新资讯、交易心得等	2	0	False	True	False	False	False	本文揭示期货交易中常见的致命陷阱，从止损、心态到认知升级，助你避开雷区，稳健盈利。	False	1297	0	9		https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/resource_server/20250430195404_1917547999404183552_786242.png	6812390c50ec085890d39d0d	探索量化交易新生态	"[
  {
    ""info_source_type"": 2,
    ""info_source_id"": ""67748456eee9135b1ce60f36"",
    ""info_source_name"": ""翌派量化"",
    ""info_source_profile"": ""https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/2atSWN4rfbhT1EGiq640PtfP.jpeg"",
    ""info_source_profile_name"": ""翌派量化"",
    ""last_update_time"": 1746013936,
    ""info_source_root"": ""mp.weixin.qq.com"",
    ""info_source_description"": ""可视化量化、策略分享、最新资讯、交易心得等"",
    ""info_source_category"": 2,
    ""rec_rank"": 0,
    ""default_select"": false,
    ""can_cancel"": true,
    ""shield"": false,
    ""is_ban"": false
  }
]"	深度解析量化策略与市场趋势	https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/feed_server/20250430225156_1917592761408901120_7373.png	2	61f13721daba4602a54f479e5b678493	True		2	10	False	"[
  ""6812390c50ec085890d39d0d""
]"
68120e1beb4dea55023c85db	7	9	大家口中的交易高手，都是“高”在哪里？期货股票交易者必读！			2025-04-30 18:02:08	https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/resource_server/20250430194945_1917546914417430528_876070.png	2	67748456eee9135b1ce60f36	翌派量化	https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/2atSWN4rfbhT1EGiq640PtfP.jpeg	翌派量化	2025-04-30 19:52:16	mp.weixin.qq.com	可视化量化、策略分享、最新资讯、交易心得等	2	0	False	True	False	False	False	成功的交易者并非依赖“神预测”，而是凭借对市场规律的深刻理解和克服内心的“作死”思维。	False	1177	0	9		https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/resource_server/20250430194945_1917546914417430528_876070.png	6812390c50ec085890d39d0d	探索量化交易新生态	"[
  {
    ""info_source_type"": 2,
    ""info_source_id"": ""67748456eee9135b1ce60f36"",
    ""info_source_name"": ""翌派量化"",
    ""info_source_profile"": ""https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/2atSWN4rfbhT1EGiq640PtfP.jpeg"",
    ""info_source_profile_name"": ""翌派量化"",
    ""last_update_time"": 1746013936,
    ""info_source_root"": ""mp.weixin.qq.com"",
    ""info_source_description"": ""可视化量化、策略分享、最新资讯、交易心得等"",
    ""info_source_category"": 2,
    ""rec_rank"": 0,
    ""default_select"": false,
    ""can_cancel"": true,
    ""shield"": false,
    ""is_ban"": false
  }
]"	深度解析量化策略与市场趋势	https://wcd-image-bucket-prod.oss-cn-zhangjiakou.aliyuncs.com/raw/feed_server/20250430225156_1917592761408901120_7373.png	2	61f13721daba4602a54f479e5b678493	True		2	10	False	"[
  ""6812390c50ec085890d39d0d""
]"
   """

    source_schema = SourceSQLSchema(
        field_names=oneline_feilds,
        field_examples=online_examples
    )
    # print(source_schema)
    result = simplify_agent.run_sync(
        "请帮忙注释数据表如下字段，不要改变格式，注释内容精简，去除非重要的字段，只保留重要的字段。",
        deps=source_schema)
    schema = "\n".join(result.data.field_comments)
    print(schema)
    """
    AgentRunResult(data=SimpleSQLSchema(field_comments=['mid：用户ID', 'name：用户名', 'sex：性别', 'level：等级', 'jointime：注册时间', 'coins：硬币数', 'vip.type：VIP类型', 'vip.status：VIP状态', 'vip.due_date：VIP到期时间', 'official.title：官方认证头衔', 'birthday：生日', 'profession.name：职业']))
    """
    print("=========================================================")
    result = simplify_agent.run_sync(
        "根据以下mysql中表结构的内容，生成select语句，只保留有注释的字段和gk_id和gk_createtime字段，并将有注释的字段重命名为字段注释名，表的结构信息如下:" + str(
            result.data.model_dump()),
        result_type=str
    )
    print(result.data)

    """
    AgentRunResult(data='根据提供的字段注释信息和要求，生成的 `SELECT` 语句将包含 `gk_id`、`gk_createtime` 以及具有注释的字段重命名后的别名。以下是生成的 `SELECT` 语句：\n\n```sql\nSELECT \n  gk_id, \n  gk_createtime, \n  mid AS 用户ID,\n  name AS 昵称,\n  sex AS 性别,\n  face AS 头像,\n  sign AS 签名,\n  rank AS 排名,\n  level AS 等级,\n  coins AS 硬币数量,\n  `vip.type` AS VIP类型,\n  `vip.status` AS VIP状态,\n  `vip.due_date` AS VIP到期时间,\n  `official.role` AS 官方角色,\n  `official.title` AS 官方标题,\n  `official.desc` AS 官方描述,\n  `pendant.name` AS 挂件名称,\n  `nameplate.name` AS 铭牌名称,\n  `live_room.roomStatus` AS 直播间状态,\n  `live_room.liveStatus` AS 直播状态,\n  `live_room.url` AS 直播链接,\n  school AS 学校,\n  birthday AS 生日,\n  `profession.name` AS 职业名称,\n  tags AS 标签,\n  is_followed AS 是否关注,\n  theme AS 主题\nFROM [表名];\n```\n\n请将 `[表名]` 替换为实际的表名称。上述 SQL 语句按照要求仅选择了包括注释的字段和指定的 `gk_id`、`gk_createtime` 字段，并将字段重命名为注释名。')
    """
