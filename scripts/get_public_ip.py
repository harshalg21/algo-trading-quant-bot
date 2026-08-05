import requests
import sys

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def get_public_ip():
    try:
        res = requests.get("https://api.ipify.org?format=json", timeout=10)
        if res.status_code == 200:
            ip = res.json().get("ip")
            print(f"PUBLIC_IP:{ip}")
            return ip
    except Exception:
        pass

    try:
        res = requests.get("https://ifconfig.me/ip", timeout=10)
        if res.status_code == 200:
            ip = res.text.strip()
            print(f"PUBLIC_IP:{ip}")
            return ip
    except Exception as e:
        print(f"Error fetching IP: {e}")
        return None

if __name__ == "__main__":
    get_public_ip()
