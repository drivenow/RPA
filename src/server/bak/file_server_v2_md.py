import os
import io
import sys
import ssl
import urllib
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from datetime import datetime, timedelta
import markdown2

class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory="E:\\RAG", **kwargs):
        if not os.path.exists(directory):
            raise ValueError(f"Directory '{directory}' does not exist")
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        # 添加安全相关的响应头
        self.send_response(200)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Content-Security-Policy', "default-src 'self'")
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return SimpleHTTPRequestHandler.do_GET(self)

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                new_parts = (parts[0], parts[1], parts[2] + '/', parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None
        try:
            self.send_response(200)
            self.send_header("Content-type", f"{ctype}; charset=utf-8")
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise

    def list_directory(self, path):
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        r = []
        displaypath = urllib.parse.unquote(self.path)
        enc = sys.getfilesystemencoding()
        title = 'Directory listing for %s' % displaypath
        r.append('<!DOCTYPE HTML>')
        r.append('<html><head>')
        r.append('<meta charset="%s">' % enc)
        r.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
        r.append('<title>%s</title>' % title)
        r.append('''
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
        </style>
        ''')
        r.append('</head>')
        r.append('<body>')
        r.append('<div class="container">')
        r.append('<h1>%s</h1>' % title)
        
        # 添加返回上级目录的链接
        parent = os.path.dirname(displaypath.rstrip('/'))
        if parent and parent != displaypath:
            r.append('<div class="parent-dir">'
                    '<a href="%s">'
                    '<span class="file-icon">↩</span>'
                    '<span>返回上级目录</span>'
                    '</a></div>' % urllib.parse.quote(parent + '/'))
        
        r.append('<ul class="file-list">')
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # 获取文件信息
            file_stat = os.stat(fullname)
            size = file_stat.st_size
            mtime = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            
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
                # 格式化文件大小
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f} KB"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                else:
                    size_str = f"{size/(1024*1024*1024):.1f} GB"
            
            # r.append(f'''<li class="file-item">
            #     <span class="file-icon">{icon}</span>
            #     <a href="{urllib.parse.quote(linkname)}" class="file-link">{displayname}</a>
            #     <span class="file-meta">{size_str}</span>
            #     <span class="file-meta">{mtime}</span>
            # </li>''')
            r.append(f'''<li class="file-item">
                <span class="file-icon">{icon}</span>
                <a href="{urllib.parse.quote(linkname)}" class="file-link">{displayname}</a>
                <span class="file-meta">{size_str}</span>
            </li>''')
        
        r.append('</ul></div></body></html>')
        encoded = ''.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def translate_markdown_to_html(self, markdown_content):
        # 按原有段落分割
        paragraphs = markdown_content.split('\n\n')
        processed_paragraphs = []
        
        for paragraph in paragraphs:
            if len(paragraph.strip()) > 200:  # 对超长段落进行处理
                sentences = []
                current_sentence = ""
                
                for char in paragraph:
                    current_sentence += char
                    # 检查是否遇到句子结束的标点符号
                    if char in ['。', '！', '？', '.', '!', '?', ';', '；']:
                        if current_sentence.strip():
                            sentences.append(current_sentence.strip())
                        current_sentence = ""
                
                # 处理最后一个句子（如果有）
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                
                # 将句子重新组合成段落
                processed_paragraphs.append('\n'.join(sentences))
            else:
                processed_paragraphs.append(paragraph.strip())
        
        # 将处理后的段落重新组合
        processed_content = '\n\n'.join(processed_paragraphs)
        
        return markdown2.markdown(processed_content)

    def serve_markdown_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            html_content = self.translate_markdown_to_html(markdown_content)
            # 添加CSS样式以优化段落布局
            styled_html = f"""
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
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(styled_html.encode('utf-8'))
        except Exception as e:
            self.send_error(404, "File not found")

    def do_GET(self):
        path = self.translate_path(self.path)
        if path.endswith('.md') or path.endswith("txt"):
            return self.serve_markdown_file(path)
        return super().do_GET()

def generate_self_signed_cert():
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # 生成证书
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u'localhost')
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u'localhost')]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # 保存证书和私钥
    cert_path = 'server.crt'
    key_path = 'server.key'
    
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(Encoding.PEM))
    
    with open(key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    return cert_path, key_path

def run_https_server(port=6001):
    # 生成证书和私钥
    cert_path, key_path = generate_self_signed_cert()
    
    # 创建HTTPS服务器
    server_address = ('', port)
    httpd = HTTPServer(server_address, SecureHTTPRequestHandler)
    
    # 配置SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f'Starting HTTPS server on port {port}...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down server...')
        httpd.server_close()
        # 清理证书文件
        os.remove(cert_path)
        os.remove(key_path)

if __name__ == '__main__':
    run_https_server()