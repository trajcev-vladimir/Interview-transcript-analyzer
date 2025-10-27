# log_utils.py
from datetime import datetime
logs = []

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tmessage=f"{timestamp} {message}"
    logs.append(tmessage)

def print_logs():
    print("\n--- LOG OUTPUT ---")
    for entry in logs:
        print(entry)

def save_logs_to_file(filename):
    """Save all logged messages to a file."""
    with open(filename, "w") as file:
        for entry in logs:
            file.write(entry + "\n")
