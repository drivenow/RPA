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
    # 请帮忙注释数据表如下字段，不要改变格式，注释内容精简，去除非重要的字段，只保留重要的字段。
    oneline_feilds = """
https://www.coze.cn/store/agent/7340211457092583465?bid=6ek0nl8hg9g09&from=bots_card&panel=1&post_id=7414699438729461811
请帮忙注释数据表“amp-api_podcasts_apple__json_data_0_.relationships.episodes.data”如下字段，不要改变格式，注释内容精简，如遇到字段包含.的，取右边字符串。
id：
type：
href：
attributes.artistName：
attributes.artwork.bgColor：
attributes.artwork.hasP3：
attributes.artwork.height：
attributes.artwork.textColor1：
attributes.artwork.textColor2：
attributes.artwork.textColor3：
attributes.artwork.textColor4：
attributes.artwork.url：
attributes.artwork.width：
attributes.artworkOrigin：
attributes.assetUrl：
attributes.contentAdvisory：
attributes.contentRating：
attributes.copyright：
attributes.description.short：
attributes.description.standard：
attributes.durationInMilliseconds：
attributes.episodeNumber：
attributes.feedUrl：
attributes.genreNames：
attributes.guid：
attributes.itunesTitle：
attributes.kind：
attributes.mediaKind：
attributes.name：
attributes.offers：
attributes.releaseDateTime：
attributes.subscribable：
attributes.url：
attributes.websiteUrl：
meta.contentVersion.MZ_INDEXER：
meta.contentVersion.RTCI：
extend：
include：
include[artists]：
views：
limit[episodes]：
limit[trailers]：
sort[trailers]：
with：
l：
    """
    online_examples = """
id	type	href	attributes.artistName	attributes.artwork.bgColor	attributes.artwork.hasP3	attributes.artwork.height	attributes.artwork.textColor1	attributes.artwork.textColor2	attributes.artwork.textColor3	attributes.artwork.textColor4	attributes.artwork.url	attributes.artwork.width	attributes.artworkOrigin	attributes.assetUrl	attributes.contentAdvisory	attributes.contentRating	attributes.copyright	attributes.description.short	attributes.description.standard	attributes.durationInMilliseconds	attributes.episodeNumber	attributes.feedUrl	attributes.genreNames	attributes.guid	attributes.itunesTitle	attributes.kind	attributes.mediaKind	attributes.name	attributes.offers	attributes.releaseDateTime	attributes.subscribable	attributes.url	attributes.websiteUrl	meta.contentVersion.MZ_INDEXER	meta.contentVersion.RTCI	extend	include	include[artists]	views	limit[episodes]	limit[trailers]	sort[trailers]	with	l
1000730774000	podcast-episodes	/v1/catalog/cn/podcast-episodes/1000730774000?l=zh-Hans-CN	科学有故事	284c7f	False	1920	ffffff	ffe6d0	d4dbe5	d4c7bf	https://is1-ssl.mzstatic.com/image/thumb/Podcasts221/v4/d1/c9/d8/d1c9d89d-8f5e-6987-55e6-d53bededf85a/mza_8774732663420438988.jpg/{w}x{h}bb.{f}	1920	episode	https://jt.ximalaya.com//GKwRIUEMu9JKAJMgHgQeZu5v.m4a?channel=rss&album_id=4156778&track_id=918730110&uid=46980604&jt=https://aod.cos.tx.xmcdn.com/storages/dd8d-audiofreehighqps/80/90/GKwRIUEMu9JKAJMgHgQeZu5v.m4a		clean	汪洁 @喜马拉雅FM	据我观察，目前社会上普遍存在两种饮食健康观念误区，一种是只要看到配料表中出现自己看不懂的化学名词就莫名恐惧，我们之前的一期音频【那些我看到“配料表干净”就拉黑的食品】就	据我观察，目前社会上普遍存在两种饮食健康观念误区，一种是只要看到配料表中出现自己看不懂的化学名词就莫名恐惧，我们之前的一期音频【那些我看到“配料表干净”就拉黑的食品】就是针对这类误区而作。另一种误区则刚好反过来，就是对各种加工食品蛮不在乎，认为只要是能合法在超市销售的食品，健康程度都差不多，爱吃就吃，完全不在乎有什么健康风险。今天这期音频，就是针对这类误区。	1190000	1	http://www.ximalaya.com/album/4156778.xml	"[
  ""自然科学""
]"	xmly_track_918730110	营养成分表中最重要的数值，9成的人却从来不看	full	audio	营养成分表中最重要的数值，9成的人却从来不看	"[
  {
    ""kind"": ""get"",
    ""type"": ""STDQ""
  }
]"	2025/10/8 7:13:26	True	https://podcasts.apple.com/cn/podcast/%E8%90%A5%E5%85%BB%E6%88%90%E5%88%86%E8%A1%A8%E4%B8%AD%E6%9C%80%E9%87%8D%E8%A6%81%E7%9A%84%E6%95%B0%E5%80%BC-9%E6%88%90%E7%9A%84%E4%BA%BA%E5%8D%B4%E4%BB%8E%E6%9D%A5%E4%B8%8D%E7%9C%8B/id1163969355?i=1000730774000	https://www.ximalaya.com/sound/918730110	1759910648022	0	availableEpisodeCount,editorialArtwork,feedUrl,sellerInfo,upsell,userRating	artists,episodes,genres,participants,reviews,trailers	podcasts	listeners-also-subscribed,channel-top-paid-shows	15	15	-releaseDate	entitlements,showHero	zh-Hans-CN
1000730591375	podcast-episodes	/v1/catalog/cn/podcast-episodes/1000730591375?l=zh-Hans-CN	科学有故事	284c7f	False	1920	ffffff	ffe6d0	d4dbe5	d4c7bf	https://is1-ssl.mzstatic.com/image/thumb/Podcasts221/v4/e5/45/7e/e5457e62-856a-de62-0b8d-e2cb8fb3905a/mza_2692154151624816040.jpg/{w}x{h}bb.{f}	1920	episode	https://jt.ximalaya.com//GKwRIasMup27AIa5XgQd1d9U.m4a?channel=rss&album_id=4156778&track_id=918433638&uid=46980604&jt=https://aod.cos.tx.xmcdn.com/storages/8ba9-audiofreehighqps/D0/00/GKwRIasMup27AIa5XgQd1d9U.m4a		clean	汪洁 @喜马拉雅FM		"2025诺贝尔生理学或医学奖解读
诺贝尔奖"	1090000	2	http://www.ximalaya.com/album/4156778.xml	"[
  ""自然科学""
]"	xmly_track_918433638	2025 诺贝尔生理学或医学奖解读	full	audio	2025 诺贝尔生理学或医学奖解读	"[
  {
    ""kind"": ""get"",
    ""type"": ""STDQ""
  }
]"	2025/10/7 9:17:12	True	https://podcasts.apple.com/cn/podcast/2025-%E8%AF%BA%E8%B4%9D%E5%B0%94%E7%94%9F%E7%90%86%E5%AD%A6%E6%88%96%E5%8C%BB%E5%AD%A6%E5%A5%96%E8%A7%A3%E8%AF%BB/id1163969355?i=1000730591375	https://www.ximalaya.com/sound/918433638	1759908307386	0	availableEpisodeCount,editorialArtwork,feedUrl,sellerInfo,upsell,userRating	artists,episodes,genres,participants,reviews,trailers	podcasts	listeners-also-subscribed,channel-top-paid-shows	15	15	-releaseDate	entitlements,showHero	zh-Hans-CN

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
