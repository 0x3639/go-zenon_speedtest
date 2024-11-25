import re
import sqlite3
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime
import logging
from datetime import datetime
import traceback

# Set up logging
logging.basicConfig(
    filename='log_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database setup
DB_NAME = 'log_data.db'

def setup_database(db_name='log_data.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='logs'
    """)
    table_exists = cursor.fetchone() is not None
    
    # Only create table if it doesn't exist
    if not table_exists:
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
        print("Created new logs table")
    else:
        print("Using existing logs table")
    
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
        self.last_height = None
        logging.info(f"Initializing LogMonitor with database: {db_name}")
        setup_database(self.db_name)
        
    def process_log_entry(self, line):
        try:
            pattern = r"Height: (\d+), Hash: ([a-f0-9]+).*?Timestamp: (\d+), Pillar producer address: ([a-z0-9]+), Current time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}), Txs: (\d+)"
            match = re.search(pattern, line)
            
            if match:
                height = int(match.group(1))
                
                # Log if we skip momentums
                if self.last_height is not None:
                    expected_height = self.last_height + 1
                    if height > expected_height:
                        logging.warning(f"Missed momentums: expected {expected_height}, got {height}")
                    elif height < self.last_height:
                        logging.warning(f"Height went backwards: was {self.last_height}, now {height}")
                
                self.last_height = height
                
                # Get other values from match
                hash_value = match.group(2)
                block_timestamp = int(match.group(3))
                pillar_address = match.group(4)
                current_time = match.group(5)
                txs = int(match.group(6))

                try:
                    # Get system resource usage
                    cpu_usage = psutil.cpu_percent(interval=0.1)
                    memory_usage = psutil.virtual_memory().percent
                    swap_usage = psutil.swap_memory().percent
                except Exception as e:
                    logging.error(f"Error getting system metrics: {str(e)}")
                    cpu_usage = memory_usage = swap_usage = 0

                try:
                    # Insert into database
                    insert_into_db(height, hash_value, block_timestamp, current_time, 
                                 pillar_address, txs, cpu_usage, memory_usage, 
                                 swap_usage, self.db_name)
                    
                    if height % 1000 == 0:  # Log every 1000 momentums
                        logging.info(f"Processed momentum height: {height}")
                        
                except Exception as e:
                    logging.error(f"Database insertion error at height {height}: {str(e)}")
                    logging.error(traceback.format_exc())
            
            else:
                logging.debug(f"Line did not match pattern: {line[:100]}...")  # Log first 100 chars
                
        except Exception as e:
            logging.error(f"Error processing log entry: {str(e)}")
            logging.error(f"Problematic line: {line[:100]}...")
            logging.error(traceback.format_exc())

class LogHandler(FileSystemEventHandler):
    def __init__(self, log_file, monitor):
        self.log_file = log_file
        self.monitor = monitor
        self.last_position = 0
        logging.info(f"Initialized LogHandler for file: {log_file}")

    def on_modified(self, event):
        try:
            if event.src_path == self.log_file:
                with open(self.log_file, 'r') as file:
                    file.seek(self.last_position)
                    new_lines = file.readlines()
                    self.last_position = file.tell()
                    for line in new_lines:
                        self.monitor.process_log_entry(line)
        except Exception as e:
            logging.error(f"Error in file handling: {str(e)}")
            logging.error(traceback.format_exc())

def monitor_log(log_file, db_name='log_data.db'):
    try:
        monitor = LogMonitor(db_name)
        event_handler = LogHandler(log_file, monitor)
        observer = Observer()
        observer.schedule(event_handler, path=log_file, recursive=False)
        observer.start()
        logging.info(f"Started monitoring log file: {log_file}")
        
        while True:
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"Fatal error in monitor_log: {str(e)}")
        logging.error(traceback.format_exc())
        raise
    finally:
        logging.info("Stopping observer")
        observer.stop()
        observer.join()

if __name__ == "__main__":
    LOG_FILE_PATH = '/var/log/syslog'  # Replace with your actual log file path
    monitor_log(LOG_FILE_PATH)