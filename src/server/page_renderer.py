import os
import io
import sys
import urllib
from datetime import datetime
import markdown2

class PageRenderer:
    def __init__(self):
        self.enc = sys.getfilesystemencoding()

    def render_directory_listing(self, path, displaypath, file_list):
        """渲染目录列表页面"""
        r = []
        title = f'Directory listing for {displaypath}'
        
        # 添加HTML头部
        r.extend(self._generate_html_header(title))
        r.extend(self._generate_css_styles())
        r.append('</head>')
        r.append('<body>')
        r.append('<div class="container">')
        r.append(f'<h1>{title}</h1>')
        # 添加链接输入表单
        r.append('''
        <div class="url-input-form">
            <form action="/process_url" method="post">
                <input type="url" name="target_url" placeholder="请输入网页链接" required>
                <button type="submit">处理链接</button>
            </form>
        </div>
        ''')
        
        # 添加返回上级目录的链接
        parent = os.path.dirname(displaypath.rstrip('/'))
        if parent and parent != displaypath:
            r.append(self._generate_parent_directory_link(parent))
        
        # 生成文件列表
        r.append('<ul class="file-list">')
        for name in sorted(file_list, key=lambda a: a.lower()):
            r.append(self._generate_file_list_item(path, name))
        
        r.append('</ul></div></body></html>')
        return ''.join(r).encode(self.enc, 'surrogateescape')

    def render_markdown(self, content):
        """渲染Markdown内容为HTML"""
        html_content = self._process_markdown_content(content)
        return self._wrap_markdown_with_template(html_content)

    def _generate_html_header(self, title):
        return [
            '<!DOCTYPE HTML>',
            '<html><head>',
            f'<meta charset="{self.enc}">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f'<title>{title}</title>'
        ]

    def _generate_css_styles(self):
        return ['''
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 20px;
            }
            h1 {
                color: #2c3e50;
                font-size: 24;
                margin-bottom: 10px;
            }
            .file-list {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            .file-item {
                display: flex;
                align-items: center;
                padding: 12px;
                border-bottom: 1px solid #eee;
                transition: background-color 0.2s;
            }
            .file-item:hover {
                background-color: #f8f9fa;
            }
            .file-item:last-child {
                border-bottom: none;
            }
            .file-icon {
                margin-right: 12px;
                color: #666;
                width: 20px;
                text-align: center;
            }
            .file-link {
                flex-grow: 1;
                text-decoration: none;
                color: #2c3e50;
            }
            .file-link:hover {
                color: #0056b3;
            }
            .file-meta {
                color: #666;
                font-size: 0.9em;
                margin-left: 20px;
            }
            .parent-dir {
                margin-bottom: 20px;
            }
            .parent-dir a {
                color: #666;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
            }
            .parent-dir a:hover {
                color: #0056b3;
            }
            .url-input-form {
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 4px;
            }
            .url-input-form form {
                display: flex;
                gap: 10px;
            }
            .url-input-form input[type="url"] {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
            }
            .url-input-form button {
                padding: 8px 16px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .url-input-form button:hover {
                background: #0056b3;
            }
        </style>
        ''']

    def _generate_parent_directory_link(self, parent):
        return ('<div class="parent-dir">' 
                f'<a href="{urllib.parse.quote(parent + "/")}">' 
                '<span class="file-icon">↩</span>' 
                '<span>返回上级目录</span>' 
                '</a></div>')

    def _generate_file_list_item(self, path, name):
        fullname = os.path.join(path, name)
        displayname = linkname = name
        
        # 获取文件信息
        file_stat = os.stat(fullname)
        size = file_stat.st_size
        
        # 确定文件类型和图标
        if os.path.isdir(fullname):
            displayname = name
            linkname = name + "/"
            icon = "📁"
            size_str = "-"
        elif os.path.islink(fullname):
            displayname = name
            icon = "🔗"
            size_str = "-"
        else:
            icon = "📄"
            size_str = self._format_file_size(size)
        
        return f'''<li class="file-item">
            <span class="file-icon">{icon}</span>
            <a href="{urllib.parse.quote(linkname)}" class="file-link">{displayname}</a>
            <span class="file-meta">{size_str}</span>
        </li>'''

    def _format_file_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        return f"{size/(1024*1024*1024):.1f} GB"

    def _process_markdown_content(self, content):
        paragraphs = content.split('\n\n')
        processed_paragraphs = []
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) > 200:  # 对超长段落进行处理
                sentences = []
                current_sentence = ""
                
                for char in paragraph:
                    current_sentence += char
                    if char in ['。', '！', '？', '.', '!', '?', ';', '；']:
                        if current_sentence.strip():
                            sentences.append(current_sentence.strip())
                        current_sentence = ""
                
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                
                processed_paragraphs.append('\n'.join(sentences))
            else:
                processed_paragraphs.append(paragraph.strip())
        
        processed_content = '\n\n'.join(processed_paragraphs)
        return markdown2.markdown(processed_content)

    def _wrap_markdown_with_template(self, html_content):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.8;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                    letter-spacing: 0.3px;
                }}
                p {{
                    margin-bottom: 1.5em;
                    text-align: justify;
                    max-width: 100ch;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    hyphens: auto;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 1.5em;
                    margin-bottom: 0.8em;
                    color: #2c3e50;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                code {{
                    font-family: 'Courier New', Courier, monospace;
                }}
                blockquote {{
                    border-left: 4px solid #42b983;
                    padding-left: 15px;
                    color: #666;
                    margin: 1em 0;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """