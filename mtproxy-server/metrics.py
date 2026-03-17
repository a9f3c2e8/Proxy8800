"""API метрик для статус-страницы 8800.life"""
import json
import time
import subprocess
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

START_TIME = time.time()


def get_cpu():
    try:
        proc = '/host/proc' if os.path.exists('/host/proc/stat') else '/proc'
        with open(f'{proc}/stat') as f:
            line = f.readline()
        vals = list(map(int, line.split()[1:]))
        idle = vals[3]
        total = sum(vals)
        time.sleep(0.1)
        with open(f'{proc}/stat') as f:
            line = f.readline()
        vals2 = list(map(int, line.split()[1:]))
        idle2 = vals2[3]
        total2 = sum(vals2)
        diff_idle = idle2 - idle
        diff_total = total2 - total
        if diff_total == 0:
            return 0
        return round((1 - diff_idle / diff_total) * 100)
    except:
        return 0


def get_ram():
    try:
        proc = '/host/proc' if os.path.exists('/host/proc/meminfo') else '/proc'
        with open(f'{proc}/meminfo') as f:
            lines = f.readlines()
        info = {}
        for line in lines:
            parts = line.split()
            info[parts[0].rstrip(':')] = int(parts[1])
        total = info.get('MemTotal', 1)
        avail = info.get('MemAvailable', 0)
        used = total - avail
        return round(used / total * 100), round(total / 1024), round(used / 1024)
    except:
        return 0, 0, 0


def get_disk():
    try:
        st = os.statvfs('/')
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        return round(used / total * 100), round(total / (1024**3)), round(used / (1024**3))
    except:
        return 0, 0, 0


def get_connections():
    try:
        result = subprocess.run(
            ['ss', '-tn', 'state', 'established'],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        count = 0
        for line in lines[1:]:
            if ':1080' in line or ':8800' in line:
                count += 1
        return count
    except:
        return 0


def get_uptime():
    try:
        proc = '/host/proc' if os.path.exists('/host/proc/uptime') else '/proc'
        with open(f'{proc}/uptime') as f:
            seconds = float(f.readline().split()[0])
        hours = int(seconds / 3600)
        days = hours // 24
        h = hours % 24
        return days, h, int(seconds)
    except:
        return 0, 0, 0


def get_ping():
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', '149.154.167.51'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'time=' in line:
                t = line.split('time=')[1].split()[0]
                return round(float(t), 1)
        return 0
    except:
        return 0


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/metrics':
            cpu = get_cpu()
            ram_pct, ram_total, ram_used = get_ram()
            disk_pct, disk_total, disk_used = get_disk()
            conns = get_connections()
            days, hours, uptime_sec = get_uptime()
            ping = get_ping()

            data = {
                'cpu': cpu,
                'ram': {'percent': ram_pct, 'total_mb': ram_total, 'used_mb': ram_used},
                'disk': {'percent': disk_pct, 'total_gb': disk_total, 'used_gb': disk_used},
                'connections': conns,
                'max_connections': 500,
                'uptime': {'days': days, 'hours': hours, 'seconds': uptime_sec},
                'ping_dc2': ping,
                'status': 'online',
                'node': 'NL-AMS-01',
                'location': 'Амстердам, NL',
                'protocol': 'MTProto TLS',
                'port': 8800,
                'timestamp': int(time.time())
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    port = 8801
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'Metrics API запущен на порту {port}')
    server.serve_forever()
