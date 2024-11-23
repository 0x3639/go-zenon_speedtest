import re
import sqlite3
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Database setup
DB_NAME = 'log_data.db'

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            height INTEGER,
            hash TEXT,
            current_time TEXT,
            txs INTEGER,
            cpu_usage REAL,
            memory_usage REAL,
            swap_usage REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_into_db(height, hash_value, current_time, txs, cpu_usage, memory_usage, swap_usage):
    """
    Insert a momentum into the database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (height, hash, current_time, txs, cpu_usage, memory_usage, swap_usage)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (height, hash_value, current_time, txs, cpu_usage, memory_usage, swap_usage))
    conn.commit()
    conn.close()
    print(f"Inserted: Height={height}, Hash={hash_value}")

# Log monitoring
class LogHandler(FileSystemEventHandler):
    def __init__(self, log_file):
        self.log_file = log_file
        self.last_position = 0  # Track the last read position in the log file

    def on_modified(self, event):
        if event.src_path == self.log_file:
            with open(self.log_file, 'r') as file:
                # Move to the last read position
                file.seek(self.last_position)

                # Read new lines
                new_lines = file.readlines()
                self.last_position = file.tell()  # Update position for next read

                # Process each new line
                for line in new_lines:
                    self.process_log_entry(line)

    def process_log_entry(self, line):
        # Regular expression to match the required log entry
        pattern = r"Height: (\d+), Hash: ([a-f0-9]+), .*?Current time: (.+?), Txs: (\d+)"
        match = re.search(pattern, line)
        if match:
            height = int(match.group(1))
            hash_value = match.group(2)
            current_time = match.group(3)
            txs = int(match.group(4))

            # Get system resource usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            swap_usage = psutil.swap_memory().percent

            # Insert into the database
            insert_into_db(height, hash_value, current_time, txs, cpu_usage, memory_usage, swap_usage)

def monitor_log(log_file):
    event_handler = LogHandler(log_file)
    observer = Observer()
    observer.schedule(event_handler, path=log_file, recursive=False)
    observer.start()
    print(f"Monitoring log file: {log_file}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    LOG_FILE_PATH = '/var/log/syslog'  # Replace with your actual log file path
    setup_database()
    monitor_log(LOG_FILE_PATH)