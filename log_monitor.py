import re
import sqlite3
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime

# Database setup
DB_NAME = 'log_data.db'

def setup_database(db_name='log_data.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        DROP TABLE IF EXISTS logs
    """)
    cursor.execute("""
        CREATE TABLE logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            height INTEGER,
            hash TEXT,
            block_timestamp INTEGER,
            date_str TEXT,
            time_str TEXT,
            timestamp DATETIME,
            pillar_address TEXT,
            txs INTEGER,
            cpu_usage REAL,
            memory_usage REAL,
            swap_usage REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_into_db(height, hash_value, block_timestamp, current_time, pillar_address, 
                  txs, cpu_usage, memory_usage, swap_usage, db_name='log_data.db'):
    
    # Split datetime into date and time parts
    date_part = current_time.split()[0]  # '2024-11-22'
    time_part = current_time.split()[1]  # '18:41:53'
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO logs (
            height, hash, block_timestamp, 
            date_str, time_str, timestamp,
            pillar_address, txs, cpu_usage, 
            memory_usage, swap_usage
        )
        VALUES (?, ?, ?, ?, ?, datetime(? || ' ' || ?), ?, ?, ?, ?, ?)
    """, (height, hash_value, block_timestamp, 
          date_part, time_part, date_part, time_part,
          pillar_address, txs, cpu_usage, memory_usage, swap_usage))
    
    conn.commit()
    conn.close()

class LogMonitor:
    def __init__(self, db_name='log_data.db'):
        self.db_name = db_name
        setup_database(self.db_name)
        
    def process_log_entry(self, line):
        pattern = r"Height: (\d+), Hash: ([a-f0-9]+).*?Timestamp: (\d+), Pillar producer address: ([a-z0-9]+), Current time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}), Txs: (\d+)"
        match = re.search(pattern, line)
        if match:
            height = int(match.group(1))
            hash_value = match.group(2)
            block_timestamp = int(match.group(3))
            pillar_address = match.group(4)
            current_time = match.group(5)
            txs = int(match.group(6))

            # Get system resource usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            swap_usage = psutil.swap_memory().percent

            # Insert into the database
            insert_into_db(height, hash_value, block_timestamp, current_time, pillar_address, 
                          txs, cpu_usage, memory_usage, swap_usage, self.db_name)

class LogHandler(FileSystemEventHandler):
    def __init__(self, log_file, monitor):
        self.log_file = log_file
        self.monitor = monitor
        self.last_position = 0

    def on_modified(self, event):
        if event.src_path == self.log_file:
            with open(self.log_file, 'r') as file:
                file.seek(self.last_position)
                new_lines = file.readlines()
                self.last_position = file.tell()
                for line in new_lines:
                    self.monitor.process_log_entry(line)

def monitor_log(log_file, db_name='log_data.db'):
    monitor = LogMonitor(db_name)
    event_handler = LogHandler(log_file, monitor)
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
    monitor_log(LOG_FILE_PATH)