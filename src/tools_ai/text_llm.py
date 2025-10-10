from langchain_community.llms import Ollama
from openai import OpenAI
import time
import random
import traceback

llm = None


def qwen_invoke(sentence):
    global llm
    if not llm:
        llm = Ollama(base_url="http://192.168.1.2:11434", model="qwen2.5:14b")
    # acquire reply content
    response = llm.invoke("以下句子换个表达，直接给出转换后的表达，无需解释：{}".format(sentence))
    print(response)
    return response


def qwen_revise_text(sentence):
    # client = OpenAI(api_key="sk-eb7b2844c60a4c88918a325417ac81f7", base_url="https://api.deepseek.com")
    # model_name = "deepseek-chat"
    client = OpenAI(api_key="sk-kcprjafyronffotrpxxovupsxzqolveqkypbmubjsopdbxec",
                    base_url="https://api.siliconflow.cn/v1")
    model_name = "Pro/deepseek-ai/DeepSeek-V3"

    # client = OpenAI(api_key="sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92",
    #                 base_url="https://api.ai-yyds.com/v1")
    # model_name = "deepseek-chat"
    # client = OpenAI(api_key="sk-CJpKFYcAMJYlKpn9721bD96f4aFc443b91D36aA0C2217a92",
    #                 base_url="http://192.168.1.2:11434/v1")
    # model_name = "llama3.1:8b"

    prompt =  f"""您的任务是校对和修改中文文本。请仔细阅读全文，识别和纠正任何语法错误，包括错别字和标点符号。
以下是您需要审阅的文本：
```
{sentence}
```
请直接给出修正后的文本，无需解释。注意不要修改和遗漏文章内容。
"""

    print(prompt)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system",
             "content": "你是一个文字校验编辑。"},
            {"role": "user", "content":prompt},
        ],
        stream=False
    )
    content = response.choices[0].message.content
    return content


def deepseek_invoke(sentence, type="tech"):
    try:
        time.sleep(random.randint(1, 5))
        print("deepseek_invoke start!")
        if type == "tech":
            # 科技类文章总结
            role_prompt = "您是一位技术媒体专家，擅长总结与技术相关的博客文章。"
            user_prompt = f"""
            您的任务是阅读和分析以下博客文章，然后提供简明的摘要，突出重点和技术方面。如果文章解释了任何原理或理论，您也应该尝试在摘要中解释这些原理或理论。
            
            以下是博客文章内容：
            <blog_post>
            {sentence}
            </blog_post>
            
            请按照以下步骤创建摘要：
            
            1. 仔细阅读和分析整个博客文章。
            2. 确定文章的主要主题和要点。
            3. 查找文章中讨论的任何技术创新、进步或独特功能。
            4. 如果文章解释了与该技术相关的任何科学原理或理论，请记下这些原理或理论。
            5. 总结内容，重点介绍所讨论技术的最重要和最有趣的方面。
            6. 如果适用，请简要解释文章中提到的任何原理或理论。
            
            您的摘要应简明扼要，信息丰富，旨在抓住博文的精髓，并强调所讨论的技术值得注意或具有创新性。
            
            请按照以下格式提供您的摘要：
            
            <summary>
            主题：[简要陈述主要主题]
            
            要点：
            1. [要点 1]
            2. [要点 2]
            3. [要点 3]
            （如有必要，请添加更多要点）
            
            技术亮点：
            [突出文章中讨论的创新或独特技术方面]
            
            原理解释：（如果适用）
            [简要解释文章中提到的任何科学原理或理论]
            
            总结：
            [简明总结博文的主要信息和在科技界的重要性]
            </summary>
            
            请记住，摘要应注重准确性和清晰度，确保您为精通技术的受众捕捉到博文的最重要方面。
            """
        elif type == "social":
            # 社科类文章总结
            role_prompt = "你是一个擅长结构化思维的专家， 通过构建一张思维框架的网(知识树)，抓住湍急的信息流中的鱼儿。"
            user_prompt = f"""您的任务是分析给定的自媒体文章，并使用结构化方法总结其关键内容。
    
            这是您需要分析的文章：
            
            <article>
            {sentence}
            </article>
            
            要分析这篇文章，请按照以下步骤操作：
            
            1. 借鉴现有的思维框架：
            - 确定可以应用于文章内容的任何通用框架或模型
            - 解释这些框架与文章中的主要思想有何关联
            
            2. 使用 5 个为什么技术寻找问题的本质：
            - 从文章中提出的主要问题或主题开始
            - 问“为什么？”五次，每次都深入探究根本原因
            - 以分层结构呈现您的发现
            
            3. 回顾类似的历史事件：
            - 找出与文章中讨论的主题有相似之处的历史事件或情况
            - 简要解释相似之处以及可以从这些历史例子中吸取哪些教训
            
            4. 分析事件顺序：
            - 将文章内容分解为按时间顺序或逻辑顺序排列的事件
            - 确定这些事件之间的因果关系
            
            完成分析后，以结构化格式呈现您的发现。使用适当的标题和副标题来组织您的想法。对每个要点进行简要说明以确保清晰度。
            
            在 <analysis> 标签内提供完整的分析。首先简要介绍文章的主要主题，然后按照上面概述的四个步骤进行结构化分析。
                            
            <analysis>
            
            思维框架：[在此处]
            
            核心观点：
            1. [第一个核心观点]
            - 支持细节1：[支持第一个观点的细节1]
            - 支持细节2：[支持第一个观点的细节2]
            （如果有更多细节请列出）
            2. [第二个核心观点]
            - 支持细节1：[支持第二个观点的细节1]
            - 支持细节2：[支持第一个观点的细节2]
             （如果有更多细节请列出）
            ...
            [根据需要继续添加其他观点，但目标是不超过 5-7 点]
            </analysis>
            
            请记住，目标是抓住文章的精髓，重点关注其最重要的观点并提供足够的细节来支持这些关键观点。您的摘要应该让读者清楚地了解文章的主要信息和论点，而无需阅读整篇文章。
            """
        elif type == "mao":
            role_prompt = "你是一个毛泽东思想专家，擅长从本质上思考问题。"
            user_prompt = f"""
            你的任务是创建关于毛泽东思想的全面和教育性学习笔记，特别关注冲突背景、解决冲突的方法以及毛泽东思想在这些过程中的作用。你是一位精通毛泽东哲学、政治意识形态和历史影响的专家，特别是在冲突及其解决方面。
            
            这是你将要分析的输入文章：
            
            <article>
            {sentence}
            </article>
            
            在分析本文并创建学习笔记时，请遵守以下准则：
            
            1. 主要关注：
            a) 文中提到或暗示的冲突背景
            b) 解决这些冲突的方法
            c) 毛泽东思想在理解和解决这些冲突中的作用和影响
            
            2. 利用你对毛泽东思想及其人生经历的广泛了解，特别是它们与冲突及其解决有关的内容。
            
            3. 提供反映中国革命历史背景和观点的见解，特别是与冲突有关的见解。
            
            4. 必要时引用毛泽东著作中的引文来支持你的观点，特别是那些与解决冲突相关的引文。
            
            5. 用毛泽东为中国背景改编的马克思列宁主义的视角来分析问题，特别是在理解和解决冲突方面。
            
            6. 讨论毛泽东思想和行动在解决冲突及其方面所做出的积极贡献和潜在的批评。
            
            在您的分析中，请结合毛泽东思想中与冲突及其解决相关的关键概念，包括但不限于：
            - 群众路线
            - 人民战争
            - 毛泽东军事思想
            - 新民主主义
            - 矛盾论
            - 实践论
            
            请按照以下步骤制定您的回复：
            1. 在毛泽东思想和其人生经历的背景下分析文章，重点关注冲突及其解决。
            2. 确定与文章中提到或暗示的冲突相关的概念、历史事件或引语。
            3. 制定全面的回复，从多个角度解决文章中与冲突相关的方面。
            4. 提供平衡的视角，承认毛泽东处理冲突的方法中的成就和潜在的缺点。
            
            请按照以下格式呈现您的回答：
            
            <thought_process>
            [您的分析和推理过程，重点关注冲突及其解决]
            </thought_process>
            
            <study_notes>
            [您对文章的最终全面学习笔记，强调冲突背景、解决方法和毛泽东思想的作用]
            </study_notes>
            
            请记住在提供最终答案之前仔细考虑您的回答。利用您对毛泽东思想及其传记的了解，给出一个合理、有见地的答案，重点关注冲突、冲突的解决以及毛泽东思想在这些过程中的作用。
          """
        elif type == "quant":
            role_prompt = "你是一个高频量化策略领域的专家，擅长分析策略的盈利逻辑和风险控制。"
            user_prompt = f"""
            您是高频量化交易策略领域的专家。您的任务是分析和总结有关高频量化交易的视频记录。请遵循以下步骤：
    
            1. 仔细阅读以下视频记录：
            
            <transcript>
           {sentence}
            </transcript>
            
            2. 分析记录并总结视频中讨论的交易思路。重点关注与高频量化交易相关的关键概念、想法和见解。
            
            3. 总结分析讲述者思路，搞明白讲述者要表达的交易理论。
             
            4. 如果记录中提到任何特定的交易策略：
            a. 识别并详细描述该策略。
            b. 分析该策略背后的盈利逻辑。
            c. 提供记录中的支持证据以供您分析。
                    
            5. 按照以下格式展示您的分析：
            
            <分析>
            <核心观点>
            [列出视频中讨论的要点和关键概念]
            </核心观点>
            
            <策略分析>
            [如果提到策略，请包括以下部分：]
            <策略描述>
            [策略的详细描述]
            </策略描述>
            
            <策略盈利逻辑>
            [策略背后的盈利逻辑分析]
            </策略盈利逻辑>
            
            <原文支撑论据>
            [支持您分析的相关引述或转述内容]
            </原文支撑论据>
            </策略分析>
            
            确保您的分析全面、结构良好且仅基于记录中提供的信息。如果记录稿中没有包含足够的信息来完成任何部分的分析，请在相关部分中清楚说明。如果策略逻辑较丰富，可以回复更多内容。
            """
        elif type == "normal":
            role_prompt = "你是一个擅长写作的专家，擅长将复杂的想法和观点用简单易懂的语言表达出来。"
            user_prompt = f"""你的任务是总结一篇自媒体文章的内容。你的目标是呈现一份全面、结构良好的总结，抓住作者的主要思想，突出重点，并在必要时提供详细的解释。
                
                以下是你需要总结的文章内容：
                
                <article_content>
                {sentence}
                </article_content>
                
                要创建有效的总结，请按照以下步骤操作：
                
                1. 仔细阅读整篇文章，了解作者的整体信息和主要论点。
                
                2. 确定文章中提出的关键主题、主题和想法。
                
                3. 分析文章的结构，注意作者如何组织他们的想法和论点。
                
                4. 创建要点大纲，确保遵循作者的逻辑思路。
                
                5. 对于每个要点，确定作者提供的支持细节、示例或证据。
                
                6. 突出显示作者得出的任何特别重要或创新的想法、统计数据或结论。
                
                7. 注意作者在整篇文章中强调的任何重复出现的主题或概念。
                
                撰写摘要时，请遵循以下准则：
                
                1. 首先简短介绍文章的精髓及其主要目的。
                
                2. 构建摘要以反映作者的思维过程和原始文章中的思路。
                
                3. 使用清晰的标题和副标题来组织内容并使其易于理解。
                
                4. 在适当的情况下使用粗体文本或项目符号来强调要点。
                
                5. 对复杂的想法或中心论点提供详细解释，确保读者能够完全理解作者想要表达的信息。
                
                6. 使用过渡短语连接不同的部分和想法，保持整个摘要的流畅。
                
                7. 用一个简短的段落来总结主要内容或作者的最终信息。
                
                使用markdown格式呈现您的摘要，并使用适当的markdown格式来设置标题（例如 副标题和）和段落（分段）。在需要的地方使用markdown的加粗标签进行强调。
                
                请记住保持客观性并准确表达作者的观点，不要插入您自己的意见或解释。
            """
        else:
            return "未知类型"

        client = OpenAI(api_key="sk-eb7b2844c60a4c88918a325417ac81f7", base_url="https://api.deepseek.com")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": role_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False
        )

        content = response.choices[0].message.content
        print("deepseek_invoke success!")
    except Exception as e:
        traceback.print_exc()
        content = "summary error!"
    content = content.replace("```markdown", "").replace("```", "")
    return content


def deepseek_reasoner(sentence, type="normal"):
    try:
        client = OpenAI(api_key="sk-eb7b2844c60a4c88918a325417ac81f7", base_url="https://api.deepseek.com")
        if type == "summary":
            system_prompt = "我需要速览这篇文章的核心观点，包括一些能支持作者观点的细节、数据或结论, 以及你的分析和看法。文章内容如下："
        else:
            system_prompt = "你是个有用的助手！"

        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence}
            ],
            stream=False
        )
        content = response.choices[0].message.content
        print("deepseek_reasoner success!")
    except Exception as e:
        traceback.print_exc()
        content = "reasoner error!"
    return content


if __name__ == '__main__':
    qwen_invoke(
        "请总结下文章的核心内容，不要求全面，抓住重点内容即可, 质量优于数量，并提供一些能支持作者观点的细节、数据或结论")

    file2 = r"X:\RAG\bili2text\outputs\小王albert\【美帝霸权三头犬 01】日本，东亚搅屎棍.txt"
    file3 = r"X:\RAG\bili2text\outputs\比亚迪汉L 电机原理\比亚迪DM双模混动系统工作原理【纸上谈车17】.txt"
    file4 = r"X:\RAG\rag_data\章位福\章位福老师谈日内程序化.txt"
    file5 = r"X:\RAG\rag_data\树莓派\12 个新的和有趣的树莓派项目.txt"
    file5 = r"X:\RAG\rag_data\树莓派\12 个新的和有趣的树莓派项目.txt"
    file6 = r"X:\RAG\rag_data\像素范\俞敏洪完胜罗永浩，什么是好老板和领头羊？有些东西不只是钱衡量.txt"

    # content = "".join(
    #     open(file6, "r", encoding="utf-8").readlines())
    # print(content)

    # print(deepseek_invoke(content, type="social"))
    print(qwen_revise_text("fdasfdsafdasff"))
    # print(qwen_invoke("test"))
    raise Exception("test")
    content = """
    请帮忙注释数据表“api6-normal-lq_amemv_aweme_v2_comment_list_json_comments”如下字段，不要改变格式，注释去掉不需要的字段，如遇到字段包含.的，取右边字符串。
    cid：
    text：
    aweme_id：
    create_time：
    digg_count：
    status：
    user.uid：
    user.short_id：
    user.nickname：
    user.avatar_thumb.uri：
    user.avatar_thumb.url_list：
    user.avatar_thumb.width：
    user.avatar_thumb.height：
    user.follow_status：
    user.unique_id：
    user.is_ad_fake：
    user.followers_detail：
    user.region：
    user.commerce_user_level：
    user.platform_sync_info：
    user.secret：
    user.geofencing：
    user.follower_status：
    user.cover_url：
    user.item_list：
    user.new_story_cover：
    user.type_label：
    user.ad_cover_url：
    user.relative_users：
    user.cha_list：
    user.sec_uid：
    user.need_points：
    user.homepage_bottom_toast：
    user.can_set_geofencing：
    user.white_cover_url：
    user.user_tags：
    user.ban_user_functions：
    user.card_entries：
    user.display_info：
    user.card_entries_not_display：
    user.card_sort_priority：
    user.interest_tags：
    user.link_item_list：
    user.user_permissions：
    user.offline_info_list：
    user.signature_extra：
    user.personal_tag_list：
    user.cf_list：
    user.im_role_ids：
    user.not_seen_item_id_list：
    user.follower_list_secondary_information_struct：
    user.endorsement_info_list：
    user.text_extra：
    user.contrail_list：
    user.data_label_list：
    user.not_seen_item_id_list_v2：
    user.special_people_labels：
    user.familiar_visitor_user：
    user.avatar_schema_list：
    user.profile_mob_params：
    user.verification_permission_ids：
    user.batch_unfollow_relation_desc：
    user.batch_unfollow_contain_tabs：
    user.creator_tag_list：
    user.private_relation_list：
    reply_id：
    user_digged：
    reply_comment：
    text_extra：
    label_text：
    label_type：
    reply_comment_total：
    reply_to_reply_id：
    is_author_digged：
    stick_position：
    user_buried：
    label_list：
    is_hot：
    text_music_info：
    image_list：
    is_note_comment：
    ip_label：
    can_share：
    item_comment_total：
    level：
    video_list：
    sort_tags：
    is_user_tend_to_reply：
    content_type：
    is_folded：
    enter_from：
    query:aweme_id：
    cursor：
    count：
    address_book_access：
    gps_access：
    forward_page_type：
    channel_id：
    city：
    hotsoon_filtered_count：
    hotsoon_has_more：
    follower_count：
    is_familiar：
    page_source：
    is_fold_list：
    user_avatar_shrink：
    aweme_author：
    item_type：
    comment_aggregation：
    top_query_word：
    is_preload：
    authentication_token：
    use_url_optimize：
    service_id：
    group_id：
    comment_scene：
    preload_type：
    comment_count：
    medium_shrink：
    need_management_hint：
    use_light_optimize：
    iid：
    device_id：
    ac：
    channel：
    aid：
    app_name：
    version_code：
    version_name：
    device_platform：
    os：
    ssmix：
    device_type：
    device_brand：
    language：
    os_api：
    os_version：
    manifest_version_code：
    resolution：
    dpi：
    update_version_code：
    _rticket：
    package：
    mcc_mnc：
    first_launch_timestamp：
    last_deeplink_update_version_code：
    cpu_support64：
    host_abi：
    is_guest_mode：
    app_type：
    minor_status：
    appTheme：
    is_preinstall：
    need_personal_recommend：
    is_android_pad：
    is_android_fold：
    ts：
    cdid：
    concurrent：
    
    ------------------------------------------
    字段示例如下：
    cid	text	aweme_id	create_time	digg_count	status	user.uid	user.short_id	user.nickname	user.avatar_thumb.uri	user.avatar_thumb.url_list	user.avatar_thumb.width	user.avatar_thumb.height	user.follow_status	user.unique_id	user.is_ad_fake	user.followers_detail	user.region	user.commerce_user_level	user.platform_sync_info	user.secret	user.geofencing	user.follower_status	user.cover_url	user.item_list	user.new_story_cover	user.type_label	user.ad_cover_url	user.relative_users	user.cha_list	user.sec_uid	user.need_points	user.homepage_bottom_toast	user.can_set_geofencing	user.white_cover_url	user.user_tags	user.ban_user_functions	user.card_entries	user.display_info	user.card_entries_not_display	user.card_sort_priority	user.interest_tags	user.link_item_list	user.user_permissions	user.offline_info_list	user.signature_extra	user.personal_tag_list	user.cf_list	user.im_role_ids	user.not_seen_item_id_list	user.follower_list_secondary_information_struct	user.endorsement_info_list	user.text_extra	user.contrail_list	user.data_label_list	user.not_seen_item_id_list_v2	user.special_people_labels	user.familiar_visitor_user	user.avatar_schema_list	user.profile_mob_params	user.verification_permission_ids	user.batch_unfollow_relation_desc	user.batch_unfollow_contain_tabs	user.creator_tag_list	user.private_relation_list	reply_id	user_digged	reply_comment	text_extra	label_text	label_type	reply_comment_total	reply_to_reply_id	is_author_digged	stick_position	user_buried	label_list	is_hot	text_music_info	image_list	is_note_comment	ip_label	can_share	item_comment_total	level	video_list	sort_tags	is_user_tend_to_reply	content_type	is_folded	enter_from	sticker.id	sticker.width	sticker.height	sticker.static_url.uri	sticker.static_url.url_list	sticker.static_url.width	sticker.static_url.height	sticker.animate_url.uri	sticker.animate_url.url_list	sticker.animate_url.width	sticker.animate_url.height	sticker.sticker_type	sticker.origin_package_id	sticker.id_str	sticker.author_sec_uid	query:aweme_id	cursor	count	address_book_access	gps_access	forward_page_type	channel_id	city	hotsoon_filtered_count	hotsoon_has_more	follower_count	is_familiar	page_source	is_fold_list	user_avatar_shrink	aweme_author	item_type	comment_aggregation	is_preload	authentication_token	use_url_optimize	service_id	group_id	comment_scene	preload_type	comment_count	medium_shrink	need_management_hint	use_light_optimize	iid	device_id	ac	channel	aid	app_name	version_code	version_name	device_platform	os	ssmix	device_type	device_brand	language	os_api	os_version	manifest_version_code	resolution	dpi	update_version_code	_rticket	package	mcc_mnc	first_launch_timestamp	last_deeplink_update_version_code	cpu_support64	host_abi	is_guest_mode	app_type	minor_status	appTheme	is_preinstall	need_personal_recommend	is_android_pad	is_android_fold	ts	cdid	concurrent
    7460925147954152204	有没有恐怖密室出个idea，就是玩到一半npc说不对劲，这里不是这样的，没有这种东西，没有这个环节，然后自己沟通对讲机，然后他也被吓到的感觉，然后玩家不就更怕了吗	7460709960826096936	2025-01-18 00:40:20	5656	1	66890075800	1339847344	霂	100x100/aweme-avatar/mosaic-legacy_2e3490002e24dea5761eb	"[
    ""https://p26.douyinpic.com/aweme-avatar/mosaic-legacy_2e3490002e24dea5761eb~tplv-dy-shrink-adapter:64:64.heic?from=2064092626&s=PackSourceEnum_COMMENT_LIST&se=true&sh=64_64&sc=avatar&biz_tag=aweme_comment&l=202502081818024D1646656E97D30DAB2B"",
    ""https://p26.douyinpic.com/aweme/100x100/aweme-avatar/mosaic-legacy_2e3490002e24dea5761eb.heic?from=2064092626&s=PackSourceEnum_COMMENT_LIST&se=false&sc=avatar&biz_tag=aweme_comment&l=202502081818024D1646656E97D30DAB2B"",
    ""https://p11.douyinpic.com/aweme/100x100/aweme-avatar/mosaic-legacy_2e3490002e24dea5761eb.heic?from=2064092626&s=PackSourceEnum_COMMENT_LIST&se=false&sc=avatar&biz_tag=aweme_comment&l=202502081818024D1646656E97D30DAB2B"",
    ""https://p5.douyinpic.com/aweme/100x100/aweme-avatar/mosaic-legacy_2e3490002e24dea5761eb.heic?from=2064092626&s=PackSourceEnum_COMMENT_LIST&se=false&sc=avatar&biz_tag=aweme_comment&l=202502081818024D1646656E97D30DAB2B"",
    ""https://p26.douyinpic.com/aweme/100x100/aweme-avatar/mosaic-legacy_2e3490002e24dea5761eb.jpeg?from=2064092626&s=PackSourceEnum_COMMENT_LIST&se=false&sc=avatar&biz_tag=aweme_comment&l=202502081818024D1646656E97D30DAB2B""
    ]"	720	720	0		False		CN	0		0		0								MS4wLjABAAAAy-wFLdrnASLpHFQ02UWCE8k7qhd7XLmRaBXqlfCrM9I																																			0	0		[]		-1	73	0	False	0	False		False			0	湖北	True	52910	1		{"eco_level_3":1,"stick":1,"eco_level_7":1,"eco_level_8":1}	False	1	False	homepage_hot																7460709960826096936	0	20	2	1	1	23	320100	0	0	961426	0	0	false	64_64	MS4wLjABAAAAxyfpuLtMeU3KwUEdCfEkpkBYQwq7hie16rLa2Y8yFOc	0	0	0	MS4wLjAAAAAAJRVuLtzIGf9ilOh4Clzi-5Y71gvmkwiePuJAqg2kTLRbRqlUUbpRcJORjqa1tpJDzCmAc8fOGGBxpLGdjDI5BGKEE7pzjT83E-XNwbGfKiQ0EKwzxzQuhsjxZjAlMXap84QodcdT9YdfbxGJQqsS10Bxs1PoJLAu6aUlOWm24_M6DMEDBILkYaEGi0cBhH7zkiLlLwp1f57LbbUfrXwECsmu4QxCrCu2LAVBk4hwc8yqE5ZujQiJHd20NqzlnzKwgE_aEEhblW4tiBcEr65oUQ	0	0	0	0	2	52879	279_374	0	0	1863029258498283	2760199244630556	wifi	douyin-huidu-gw-huidu-2940	1128	aweme	290400	29.4.0	android	android	a	SM-N9700	samsung	zh	28	9	290400	1600*900	240	29400100	1739009883011	com.ss.android.ugc.aweme	46000	2025-02-06 23:18:01	0	true	arm64-v8a	0	normal	0	light	0	1	0	0	1739009882	1d485a3a-26ac-4010-b1c0-ae4819aaca49	0

    """
    # print(deepseek_reasoner(content))
