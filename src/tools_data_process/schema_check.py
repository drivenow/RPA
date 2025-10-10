import pymysql
import pandas as pd


def get_bili_data():
    """
    使用 pandas read_sql 从 b站搜索结果 表中获取前100条数据
    返回: pandas DataFrame 包含查询结果
    """
    # 数据库连接配置
    db_config = {
        'host': 'localhost',
        'user': 'admin', 
        'password': 'ybsDW246401.',
        'db': 'mydatabase',
        'charset': 'utf8'
    }
    
    # SQL 查询语句
    sql = "select * from `b站搜索结果` limit 100"
    
    try:
        # 建立数据库连接
        db = pymysql.connect(**db_config)
        
        # 使用 pandas read_sql 执行查询并转换为 DataFrame
        df = pd.read_sql(sql, db)
        
        print(f"成功获取数据，共 {len(df)} 行，{len(df.columns)} 列")
        print(f"列名: {list(df.columns)}")
        
        return df
        
    except pymysql.Error as e:
        print(f"数据库错误: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"执行错误: {e}")
        return pd.DataFrame()
    finally:
        # 确保数据库连接被关闭
        try:
            if 'db' in locals():
                db.close()
                print("数据库连接已关闭")
        except:
            pass


def filter_columns(df, target_columns):
    """
    检查指定的列是否存在于DataFrame中，只保留存在的列
    
    参数:
    df: pandas DataFrame
    target_columns: list, 目标列名列表
    
    返回:
    filtered_df: pandas DataFrame, 只包含存在的列
    existing_columns: list, 存在的列名
    missing_columns: list, 不存在的列名
    """
    if df.empty:
        print("DataFrame 为空，无法进行列筛选")
        return df, [], target_columns
    
    # 获取DataFrame中的所有列名
    df_columns = list(df.columns)
    
    # 检查哪些目标列存在于DataFrame中
    existing_columns = [col for col in target_columns if col in df_columns]
    missing_columns = [col for col in target_columns if col not in df_columns]
    
    # 打印结果
    print(f"\n=== 列筛选结果 ===")
    print(f"DataFrame 总列数: {len(df_columns)}")
    print(f"目标列数: {len(target_columns)}")
    print(f"存在的列数: {len(existing_columns)}")
    print(f"缺失的列数: {len(missing_columns)}")
    
    if existing_columns:
        print(f"\n存在的列:")
        for col in existing_columns:
            print(f"  - {col}")
    
    if missing_columns:
        print(f"\n缺失的列:")
        for col in missing_columns:
            print(f"  - {col}")
    
    # 只保留存在的列
    if existing_columns:
        filtered_df = df[existing_columns]
        print(f"\n筛选后的DataFrame形状: {filtered_df.shape}")
        return filtered_df, existing_columns, missing_columns
    else:
        print("\n警告: 没有找到任何匹配的列")
        return pd.DataFrame(), existing_columns, missing_columns


if __name__ == "__main__":
    # 测试函数
    print("开始执行 pandas read_sql 查询...")
    result_df = get_bili_data()
    
    if not result_df.empty:
        print("\n数据预览:")
        print(result_df.head())
        print(f"\nDataFrame 信息:")
        print(f"形状: {result_df.shape}")
        print(f"数据类型:\n{result_df.dtypes}")
        
        # 定义目标列
        target_columns = [
            'comment', 'typeid', 'play', 'pic', 'subtitle', 'description', 'copyright', 'title', 'review', 'author', 'mid', 'created', 'length', 'video_review', 'aid', 'bvid', 'hide_click', 'is_pay', 'is_union_video', 'is_steins_gate', 'is_live_playback', 'is_lesson_video', 'is_lesson_finished', 'lesson_update_info', 'jump_url', 'meta', 'is_avoided', 'season_id', 'attribute', 'is_charging_arc', 'elec_arc_type', 'elec_arc_badge', 'vt', 'enable_vt', 'vt_display', 'playback_position', 'is_self_view', 'view_self_type', 'meta.id', 'meta.title', 'meta.cover', 'meta.mid', 'meta.intro', 'meta.sign_state', 'meta.attribute', 'meta.stat.season_id', 'meta.stat.view', 'meta.stat.danmaku', 'meta.stat.reply', 'meta.stat.favorite', 'meta.stat.coin', 'meta.stat.share', 'meta.stat.like', 'meta.stat.mtime', 'meta.stat.vt', 'meta.stat.vv', 'meta.ep_count', 'meta.first_aid', 'meta.ptime', 'meta.ep_num', 'query:mid', 'order', 'ps', 'pn', 'index', 'order_avoided', 'platform', 'web_location', 'dm_img_list', 'dm_img_str', 'dm_cover_img_str', 'dm_img_inter', 'w_webid', 'w_rid', 'wts'
        ]
        
        # 执行列筛选
        filtered_df, existing_cols, missing_cols = filter_columns(result_df, target_columns)
        
        if not filtered_df.empty:
            print(f"\n=== 筛选后的数据预览 ===")
            print(filtered_df.head())
        
    else:
        print("未获取到数据")