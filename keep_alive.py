import threading
import requests
import time

def ping():
    url = "https://xdownloader-sf0e.onrender.com/health"

    while True:
        try:
            requests.get(url, timeout=10)
            print("🔥 Keep-alive ping sent")
        except Exception as e:
            print("⚠ Keep-alive error:", e)

        time.sleep(300)  # every 5 minutes

def start_keep_alive():
    thread = threading.Thread(target=ping)
    thread.daemon = True
    thread.start()
