#!/usr/bin/env python3
"""
调试真实HTML内容的JSON提取
"""

import re
import json
from src.extractor.advanced_json_matcher import AdvancedJSONMatcher

def debug_real_html():
    """调试真实的HTML内容"""
    
    # 您提供的HTML内容
    html_content = '''<!doctype html><html><head><script formula-runtime >function e(e){for(var r=1;r<arguments.length;r++){var t=null!=arguments[r]?arguments[r]:{},n=Object.keys(t);"function"==typeof Object.getOwnPropertySymbols&&(n=n.concat(Object.getOwnPropertySymbols(t).filter(function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),n.forEach(function(r){var n;n=t[r],r in e?Object.defineProperty(e,r,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[r]=n})}return e}function r(e,r){return r=null!=r?r:{},Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(r)):(function(e,r){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t.push.apply(t,n)}return t})(Object(r)).forEach(function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(r,t))}),e}var t,n,a,o=function(t){var n="4.0.16",a="xhs-pc-web",o="4.74.0";return r(e({},t),{context_artifactName:"formula",context_artifactVersion:n||"unknown",measurement_data:r(e({},t.measurement_data),{packageName:a||"unknown",packageVersion:o||"unknown"})})},i=function(){if("undefined"!=typeof window){var e,r,t=null===(e=window.eaglet)||void 0===e?void 0:e.push;return t||(t=null===(r=window.insight)||void 0===r?void 0:r.push),t?function(e){return t(o(e),"ApmXrayTracker")}:void 0}},c="FORMULA_ASSETS_LOAD_ERROR",u=function(){var e=localStorage.getItem(c);return e?JSON.parse(e):[]};function s(e){try{var r=i();if(r)r(e);else{var t=u();if(t.length>=1e3)return;t.push(e),localStorage.setItem(c,JSON.stringify(t))}}catch(r){console.error({error:r,errorData:e})}}try{t=function(e,r,t){var a,o=function(e){if(e){var r="//fe-static.xhscdn.com";return -1!==e.indexOf(r)?"".concat(e.replace(r,"//cdn.xiaohongshu.com"),"?business=fe&scene=feplatform"):void 0}}(e);if(!o){s({measurement_name:"reload_resource_error",measurement_data:n(t,{retryErrorType:"newUrlError",timestamp:String(Date.now())})});return}"js"===r?(a=document.createElement("script")).src=o:"css"===r&&((a=document.createElement("link")).rel="stylesheet",a.href=o),a&&(a.dataset.formulaAssetRetry="1",document.head.appendChild(a),a.addEventListener("load",function(){s({measurement_name:"reload_resource_duration",measurement_data:n(t,{duration:Date.now()-new Date(Number(t.timestamp)).getTime(),retryResourceUrl:a.src||a.href})})}),a.addEventListener("error",function(){s({measurement_name:"reload_resource_error",measurement_data:n(t,{timestamp:String(Date.now()),retryErrorType:"retryOnloadError",retryResourceUrl:a.src||a.href})})}))},n=Object.assign,a=["resource/js/bundler-runtime.83524eb5.js","resource/js/vendor-dynamic.3c0ca5ad.js","resource/js/library-polyfill.46cc9284.js","resource/js/library-axios.435de88b.js","resource/js/library-vue.a552caa8.js","resource/js/vendor.621a7319.js","resource/js/index.9f6eff67.js","resource/css/index.3fffce4c.css","resource/css/async/Notification.aa311d0c.css","resource/css/async/42.1b2bf9e1.css","resource/css/async/Note.6e3263e0.css","resource/css/async/FeedToNote.a47e232f.css","resource/css/async/minor.a7f732ec.css","resource/css/async/355.1a9a769f.css","resource/css/async/Explore.30c1e8ce.css","resource/css/async/937.de1aa713.css","resource/css/async/NPS.0fee7ba1.css","resource/css/async/User.3830129f.css","resource/css/async/953.272459c1.css","resource/css/async/Search.6e2c6bf7.css","resource/css/async/75.693a9a9c.css","resource/css/async/772.db47c221.css","resource/css/async/Login.c2772494.css","resource/css/async/Board.c56ea05c.css"],window.addEventListener("error",function(e){var r,n,o=e.target;if(o){var i=o.href||o.src;if(i){if(!(null===(r=o.dataset)||void 0===r?void 0:r.formulaCdnRetry)&&!a.some(function(e){return i.includes(e)}))return;var c=null===(n=o.dataset)||void 0===n?void 0:n.formulaAssetRetry,u="LINK"===o.tagName?"css":"js",l={measurement_name:"biz_load_error_count",measurement_data:{path:window.location.href,resourceType:u,resourceUrl:o.href||o.src||"-",timestamp:String(Date.now())}};c||(s(l),t(i,u,l.measurement_data))}}},!0),window.addEventListener("load",function(){try{var e=i();if(!e)return;var r=u();if(r.length>0){var t=!0,n=!1,a=void 0;try{for(var o,s=r[Symbol.iterator]();!(t=(o=s.next()).done);t=!0){var l=o.value;e(l)}}catch(e){n=!0,a=e}finally{try{t||null==s.return||s.return()}finally{if(n)throw a}}}localStorage.removeItem(c)}catch(e){console.error(e)}})}catch(e){console.error("formula assets retry error: ",e)}</script><script data-apm-fmp-pre-module>!function(e,r){try{var n="__FST__",t=["HTML","HEAD","META","LINK","SCRIPT","STYLE","NOSCRIPT"];e[n]=e[n]||{runned:!1,observer:null,mutaRecords:[],imgObserver:null,imgRecords:[],run:function(n){try{!n.runned&&(n.runned=!0,e.MutationObserver&&e.performance&&e.performance.now&&(n.observer=new e.MutationObserver((function(r){try{n.mutaRecords.push({mutations:r,startTime:e.performance.now()}),r.filter((function(e){var r=(e.target.nodeName||"").toUpperCase();return"childList"===e.type&&r&&-1===t.indexOf(r)&&e.addedNodes&&e.addedNodes.length})).forEach((function(r){[].slice.call(r.addedNodes,0).filter((function(e){var r=(e.nodeName||"").toUpperCase();return 1===e.nodeType&&"IMG"===r&&e.isConnected&&!e.closest("[fmp-ignore]")&&!e.hasAttribute("fmp-ignore")})).forEach((function(r){r.addEventListener("load",(function(){try{var t=e.performance.now(),o=r.getAttribute("src")||"";e.requestAnimationFrame((function i(a){try{r&&r.naturalWidth&&r.naturalHeight?n.imgRecords.push({name:o.split(":")[1]||o,responseEnd:a,loadTime:t,startTime:0,duration:0,type:"loaded"}):e.requestAnimationFrame(i)}catch(e){}}))}catch(e){}}))}))}))}catch(e){}})),n.observer.observe(r,{childList:!0,subtree:!0}),e.PerformanceObserver&&(n.imgObserver=new e.PerformanceObserver((function(e){try{e.getEntries().filter((function(e){return"img"===e.initiatorType||"css"===e.initiatorType||"link"===e.in'''
    
    print("🔍 分析真实HTML内容...")
    print(f"HTML长度: {len(html_content)} 字符")
    print()
    
    # 1. 检查是否包含小红书特定的模式
    print("📋 检查小红书特定模式:")
    patterns_to_check = {
        '__INITIAL_STATE__': r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
        '__NUXT__': r'window\.__NUXT__\s*=\s*({.+?});',
        'pageData': r'window\.pageData\s*=\s*({.+?});',
        'feedData': r'window\.feedData\s*=\s*({.+?});',
        'userData': r'window\.userData\s*=\s*({.+?});',
        'configData': r'window\.configData\s*=\s*({.+?});'
    }
    
    for name, pattern in patterns_to_check.items():
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        print(f"  {name}: {len(matches)} 个匹配")
        if matches:
            for i, match in enumerate(matches[:2]):  # 只显示前2个
                print(f"    匹配 {i+1}: {match[:100]}...")
    
    print()
    
    # 2. 检查JSON script标签
    print("📋 检查JSON script标签:")
    json_script_pattern = r'<script[^>]*type=["\']application/json["\'][^>]*>(.+?)</script>'
    json_scripts = re.findall(json_script_pattern, html_content, re.DOTALL | re.IGNORECASE)
    print(f"  JSON script标签: {len(json_scripts)} 个")
    
    # 3. 检查所有script标签
    print("📋 检查所有script标签:")
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
    print(f"  总script标签数: {len(scripts)} 个")
    
    for i, script in enumerate(scripts):
        print(f"  Script {i+1}: {len(script)} 字符")
        if len(script) > 100:
            print(f"    内容预览: {script[:200]}...")
        print()
    
    # 4. 使用AdvancedJSONMatcher测试
    print("🧪 使用AdvancedJSONMatcher测试:")
    matcher = AdvancedJSONMatcher()
    candidates = matcher.extract_and_rank_json(html_content)
    print(f"  找到 {len(candidates)} 个JSON候选")
    
    for i, candidate in enumerate(candidates):
        print(f"  候选 {i+1}:")
        print(f"    名称: {candidate['name']}")
        print(f"    类型: {candidate['pattern_type']}")
        print(f"    优先级: {candidate['priority']}")
        print(f"    价值分数: {candidate['value_score']}")
        print(f"    大小: {candidate['size']} 字符")
        print(f"    描述: {candidate['description']}")
        print(f"    原始内容: {candidate['raw']}")
        print()
    
    # 5. 手动查找可能的JSON数据
    print("🔍 手动查找可能的JSON数据:")
    
    # 查找大括号对
    brace_count = html_content.count('{')
    print(f"  大括号数量: {brace_count}")
    
    # 查找可能的JSON对象（简单启发式）
    possible_json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    possible_jsons = re.findall(possible_json_pattern, html_content)
    print(f"  可能的JSON对象: {len(possible_jsons)} 个")
    
    for i, pj in enumerate(possible_jsons[:3]):  # 只显示前3个
        if len(pj) > 50:  # 只显示较大的对象
            print(f"    对象 {i+1}: {len(pj)} 字符")
            print(f"      内容: {pj[:100]}...")
            
            # 尝试解析
            try:
                parsed = json.loads(pj)
                print(f"      ✅ 可解析为JSON")
                if isinstance(parsed, dict):
                    print(f"      键: {list(parsed.keys())[:5]}")
            except:
                print(f"      ❌ 无法解析为JSON")
            print()

if __name__ == "__main__":
    debug_real_html()