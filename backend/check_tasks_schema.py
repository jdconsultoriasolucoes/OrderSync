import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def check_background_tasks_schema():
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment.")
        return
        
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print(f"Checking schema for table: tb_background_tasks")
        cursor.execute("""
            SELECT column_name, is_nullable, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'tb_background_tasks'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[0]:<20} | Nullable: {col[1]:<5} | Type: {col[2]}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_background_tasks_schema()
