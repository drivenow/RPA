import time
from loguru import logger

def convert_cookies_for_playwright(raw_cookies):
    """
    将原始 Cookie 格式转换为 Playwright 兼容格式
    
    参数:
        raw_cookies: list[dict] - 原始 Cookie 数据列表
        
    返回:
        list[dict] - Playwright 兼容的 Cookie 格式
    """
    playwright_cookies = []
    
    for cookie in raw_cookies:
        # 检查必要字段是否存在
        if not all(key in cookie for key in ['name', 'value', 'domain', 'path']):
            logger.warning(f"跳过无效的 Cookie: {cookie.get('name', 'unknown')}")
            continue
        
        # 转换时间格式: expirationDate (浮点) → expires (整数秒)
        expires = None
        if 'expirationDate' in cookie:
            # 转换为整数秒（丢弃小数部分）
            expires = int(cookie['expirationDate'])
            # 检查是否过期
            if expires < time.time():
                logger.warning(f"Cookie 已过期: {cookie['name']} (expires: {expires})")
                continue
                
        # 转换 sameSite 值
        same_site = cookie.get('sameSite', 'Lax')
        same_site_mapping = {
            'no_restriction': 'None',
            'unspecified': 'Lax',
            'lax': 'Lax',
            'strict': 'Strict'
        }
        same_site = same_site_mapping.get(same_site.lower(), same_site)
        
        # 转换为 Playwright 格式
        playwright_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie['path'],
            'expires': expires,  # 可以为 None (会话 Cookie)
            'httpOnly': cookie.get('httpOnly', False),
            'secure': cookie.get('secure', False),
            'sameSite': same_site
        }
        
        # 特殊处理：确保 sameSite=None 时设置 secure=True
        if same_site == 'None' and not playwright_cookie['secure']:
            logger.info(f"强制为 SameSite=None 的 Cookie {cookie['name']} 启用 secure")
            playwright_cookie['secure'] = True
            
        playwright_cookies.append(playwright_cookie)
    
    return playwright_cookies