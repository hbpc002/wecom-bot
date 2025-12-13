import logging
from datetime import date
from database import Database
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_lock():
    db_path = 'data/test_lock.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        
    logging.info("Starting lock test...")
    
    # Initialize database
    db = Database(db_path)
    
    task_name = "test_task"
    task_date = date(2025, 1, 1)
    
    # First attempt - should succeed
    logging.info("Attempting to acquire lock (1st time)...")
    if db.acquire_task_lock(task_name, task_date):
        logging.info("SUCCESS: Lock acquired.")
    else:
        logging.error("FAILURE: Failed to acquire lock on first attempt.")
        
    # Second attempt - should fail
    logging.info("Attempting to acquire lock (2nd time)...")
    if not db.acquire_task_lock(task_name, task_date):
        logging.info("SUCCESS: Lock acquisition failed as expected.")
    else:
        logging.error("FAILURE: Acquired lock on second attempt (should have failed).")
        
    # Different task name - should succeed
    logging.info("Attempting to acquire lock for different task...")
    if db.acquire_task_lock("other_task", task_date):
        logging.info("SUCCESS: Lock acquired for different task.")
    else:
        logging.error("FAILURE: Failed to acquire lock for different task.")
        
    # Different date - should succeed
    logging.info("Attempting to acquire lock for different date...")
    if db.acquire_task_lock(task_name, date(2025, 1, 2)):
        logging.info("SUCCESS: Lock acquired for different date.")
    else:
        logging.error("FAILURE: Failed to acquire lock for different date.")

    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    logging.info("Test completed.")

if __name__ == "__main__":
    test_lock()
