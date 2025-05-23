# Simple wrapper script to run the test_sql.py file
import test_sql

if __name__ == "__main__":
    print("Running SQL Compiler Test...")
    test_sql.test_sql()
    print("\nTest completed.")
