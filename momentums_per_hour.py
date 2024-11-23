import sqlite3
from datetime import datetime
from tabulate import tabulate

# Database file name
DB_NAME = 'log_data.db'

def calculate_momentums_per_hour():
    # Connect to the SQLite database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query to fetch timestamps and heights using the new timestamp field
    query = """
        SELECT timestamp, height
        FROM logs
        ORDER BY timestamp ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    if not rows or len(rows) < 2:
        print("Not enough data to calculate momentums per hour.")
        return []

    # Parse data and calculate momentums per hour
    hourly_data = []
    start_time = datetime.strptime(rows[0][0], "%Y-%m-%d %H:%M:%S")
    start_height = rows[0][1]
    total_momentums = 0

    for current_time_str, height in rows[1:]:
        current_time = datetime.strptime(current_time_str, "%Y-%m-%d %H:%M:%S")
        elapsed_hours = (current_time - start_time).total_seconds() / 3600

        if elapsed_hours >= 1:
            # Calculate momentums per hour
            momentums_per_hour = total_momentums / elapsed_hours
            hourly_data.append((start_time.strftime("%Y-%m-%d %H:%M:%S"), momentums_per_hour))
            
            # Reset start time and momentums
            start_time = current_time
            total_momentums = 0

        total_momentums += height - start_height
        start_height = height

    return hourly_data

def display_results(hourly_data):
    # Display the results in a table
    if not hourly_data:
        print("No data available.")
        return

    headers = ["Start Time", "Momentums per Hour"]
    print(tabulate(hourly_data, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    print("Calculating momentums per hour...")
    hourly_data = calculate_momentums_per_hour()
    display_results(hourly_data)