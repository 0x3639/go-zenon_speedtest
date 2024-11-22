# Log Monitor with System Resource Tracking

This Python script monitors a log file for specific entries, extracts relevant information (block height, hash, timestamp, number of transactions, and system resource usage), and stores the data in a SQLite database.

---

## Features

- Real-time monitoring of the log file.
- Extracts:
  - Block height
  - Block hash
  - Timestamp
  - Number of transactions
  - System resource usage (CPU, memory, and swap usage).
- Stores the extracted data in a SQLite database for analysis.

---

## Requirements

- Python 3.7 or higher
- Libraries:
  - `watchdog` for file monitoring
  - `psutil` for system resource tracking

---

## Setup Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/0x3639/go-zenon_speedtest.git
cd go-zenon_speedtest
```

### Step 2: Create and Activate a Virtual Environment

It’s recommended to use a virtual environment to manage dependencies.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

Use the provided `requirements.txt` file to install the necessary libraries.

```bash
pip install -r requirements.txt
```

---

## Configuration

Update the path to your log file in the script (`LOG_FILE_PATH` variable):

```python
LOG_FILE_PATH = '/var/lol/syslog'  # Replace with your actual log file path
```

---

## Running the Script

### Run in Foreground

To start monitoring the log file, run:

```bash
python log_monitor.py
```

### Run as a Background Service (Linux/Mac)

#### Option 1: Using `nohup`

Run the script with `nohup` to allow it to keep running after the terminal is closed:

```bash
nohup python log_monitor.py > log_monitor.out 2>&1 &
```

- **`nohup`**: Ensures the script keeps running after the terminal closes.
- **`> log_monitor.out`**: Redirects output to a file (`log_monitor.out`).
- **`2>&1`**: Redirects error messages to the same file.

To stop the script later, find its process ID (PID) using:

```bash
ps aux | grep log_monitor.py
```

Then kill the process:

```bash
kill <PID>
```

#### Option 2: Using `systemd`

1. Create a `systemd` service file:

   ```bash
   sudo nano /etc/systemd/system/log_monitor.service
   ```

2. Add the following content to the file:

   ```ini
   [Unit]
   Description=Log Monitor Service
   After=network.target

   [Service]
   ExecStart=/path/to/venv/bin/python /path/to/go-zenon_speedtest/log_monitor.py
   WorkingDirectory=/path/to/go-zenon_speedtest
   StandardOutput=file:/path/to/go-zenon_speedtest/log_monitor.log
   StandardError=file:/path/to/go-zenon_speedtest/log_monitor_error.log
   Restart=always
   User=<your-username>

   [Install]
   WantedBy=multi-user.target
   ```

   Replace `/path/to/...` with the actual paths to your project and virtual environment. Replace `<your-username>` with your Linux username.

3. Reload `systemd` and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start log_monitor.service
   ```

4. Enable the service to run on boot:

   ```bash
   sudo systemctl enable log_monitor.service
   ```

5. Check the service status:

   ```bash
   sudo systemctl status log_monitor.service
   ```

### Run in Background (Windows)

#### Option 1: Using `pythonw`

Rename `log_monitor.py` to `log_monitor.pyw` and run it with `pythonw`:

```cmd
pythonw log_monitor.pyw
```

This runs the script without a terminal.

#### Option 2: Using Task Scheduler

1. Open Task Scheduler.
2. Create a new task.
3. Set the action to run your Python executable with the script as an argument:
   ```cmd
   python.exe C:\path\to\log_monitor.py
   ```

---

## Database Details

The script creates a SQLite database (`log_data.db`) with the following schema:

| Column        | Type    | Description                              |
|---------------|---------|------------------------------------------|
| `id`          | INTEGER | Auto-incrementing ID                    |
| `height`      | INTEGER | Block height                            |
| `hash`        | TEXT    | Block hash                              |
| `current_time`| TEXT    | Timestamp of the entry                  |
| `txs`         | INTEGER | Number of transactions in the block     |
| `cpu_usage`   | REAL    | CPU usage percentage                    |
| `memory_usage`| REAL    | Memory usage percentage                 |
| `swap_usage`  | REAL    | Swap usage percentage                   |

---

## Troubleshooting

- Ensure the log file path is correct and accessible.
- If libraries are missing, ensure dependencies are installed:
  ```bash
  pip install -r requirements.txt
  ```

---

## License

This project is licensed under the MIT License.

---

Let me know if you need further assistance or would like me to include this in your repository!