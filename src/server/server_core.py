import os
import io
import ssl
import urllib
from http.server import HTTPServer, SimpleHTTPRequestHandler
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from datetime import datetime, timedelta
from page_renderer import PageRenderer

class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory="E:\\RAG", **kwargs):
        if not os.path.exists(directory):
            raise ValueError(f"Directory '{directory}' does not exist")
        self.page_renderer = PageRenderer()
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
            file_list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        
        displaypath = urllib.parse.unquote(self.path)
        encoded = self.page_renderer.render_directory_listing(path, displaypath, file_list)
        
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=%s" % self.page_renderer.enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def serve_markdown_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            html_content = self.page_renderer.render_markdown(markdown_content)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            self.send_error(404, "File not found")

    def do_GET(self):
        path = self.translate_path(self.path)
        if path.endswith('.md') or path.endswith("txt"):
            return self.serve_markdown_file(path)
        return super().do_GET()

    def do_POST(self):
        if self.path == '/process_url':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            # 解析表单数据
            form_data = urllib.parse.parse_qs(post_data)
            target_url = form_data.get('target_url', [''])[0]
            
            if target_url:
                # 这里可以添加处理链接的逻辑
                response = f'收到链接: {target_url}'
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
            else:
                self.send_error(400, "Missing target URL")
        else:
            self.send_error(404, "Not Found")

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
    server_address = ('0.0.0.0', port)
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