import unittest
import sqlite3
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from log_monitor import LogMonitor, setup_database, insert_into_db

class TestLogMonitor(unittest.TestCase):
    def setUp(self):
        # Use a test database file
        self.TEST_DB = 'test_log_data.db'
        
        # Sample log entries
        self.test_log_entry = """Nov 22 18:41:53 tetonflats znnd[45297]: [Momentum inserted] Height: 485600, Hash: e7dcdd58b008179b550370bf29e9d224758a3edfc16f774079df509fddb2b01e, Timestamp: 1642814430, Pillar producer address: z1qrmy8crwgg56mjuwmetpjwkh2tsqjwyh3rsh9u, Current time: 2024-11-22 18:41:53, Txs: 0"""
        
        # Set up a fresh test database
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)
        setup_database(self.TEST_DB)
        
        # Initialize the log monitor with test database
        self.log_monitor = LogMonitor(self.TEST_DB)

    def tearDown(self):
        # Clean up the test database
        if os.path.exists(self.TEST_DB):
            os.remove(self.TEST_DB)

    def test_log_entry_parsing(self):
        """Test that log entries are parsed correctly"""
        self.log_monitor.process_log_entry(self.test_log_entry)
        
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT height, hash, block_timestamp, timestamp,
                   pillar_address, txs
            FROM logs
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        print(f"Debug - Retrieved from database: {row}")
        conn.close()
        
        # Verify each field
        self.assertEqual(row[0], 485600)  # height
        self.assertEqual(row[1], "e7dcdd58b008179b550370bf29e9d224758a3edfc16f774079df509fddb2b01e")  # hash
        self.assertEqual(row[2], 1642814430)  # block_timestamp
        self.assertEqual(row[3], "2024-11-22 18:41:53")  # timestamp
        self.assertEqual(row[4], "z1qrmy8crwgg56mjuwmetpjwkh2tsqjwyh3rsh9u")  # pillar_address
        self.assertEqual(row[5], 0)  # txs

    def test_multiple_log_entries(self):
        """Test processing multiple log entries"""
        # Create a second test entry with different values
        test_log_entry2 = self.test_log_entry.replace("485600", "485601")
        
        # Process both entries
        self.log_monitor.process_log_entry(self.test_log_entry)
        self.log_monitor.process_log_entry(test_log_entry2)
        
        # Verify entries are stored with correct timestamps
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT height, timestamp
            FROM logs
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 2)  # Verify we have two entries
        self.assertEqual(rows[0][1], "2024-11-22 18:41:53")  # Verify timestamp format

    def test_invalid_log_entry(self):
        """Test handling of invalid log entries"""
        invalid_entry = "This is not a valid log entry"
        
        # This should not raise an exception
        self.log_monitor.process_log_entry(invalid_entry)
        
        # Verify nothing was inserted
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 0)

    def test_timestamp_ordering(self):
        """Test that records are properly ordered by timestamp"""
        # Process multiple entries
        self.log_monitor.process_log_entry(self.test_log_entry)
        
        # Create and process an entry with a different timestamp
        modified_entry = self.test_log_entry.replace("18:41:53", "19:41:53")
        self.log_monitor.process_log_entry(modified_entry)
        
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp
            FROM logs
            ORDER BY timestamp DESC
        """)
        timestamps = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Verify timestamps are in correct order
        self.assertEqual(timestamps[0], "2024-11-22 19:41:53")
        self.assertEqual(timestamps[1], "2024-11-22 18:41:53")

if __name__ == '__main__':
    unittest.main() 