import sqlite3
from tabulate import tabulate

# Database file name
DB_NAME = 'log_data.db'

def fetch_last_25_records():
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Query to fetch the last 25 records
    query = """
        SELECT id, height, hash, current_time,
               txs, cpu_usage, memory_usage, swap_usage
        FROM logs
        ORDER BY id DESC
        LIMIT 25;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def display_table(records):
    # Define table headers
    headers = ["ID", "Height", "Hash", "Current Time",
              "Txs", "CPU Usage (%)", "Memory Usage (%)", "Swap Usage (%)"]
    
    # Display the records in a table format
    print(tabulate(records, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    print("Fetching the last 25 log entries...")
    records = fetch_last_25_records()
    if records:
        display_table(records)
    else:
        print("No records found in the database.")