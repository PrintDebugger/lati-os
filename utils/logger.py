from datetime import datetime

def log(message):
    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[{0}] {1}".format(formatted_time, message))