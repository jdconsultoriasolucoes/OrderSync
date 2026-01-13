import os
# Hardcoded for debugging purposes - keeping consistency with previous tools
os.environ["DATABASE_URL"] = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

from sqlalchemy import text
from database import SessionLocal

def migrate_familia():
    db = SessionLocal()
    try:
        print("Starting migration of t_familia_produtos...")
        
        # 1. Check if column 'familia_carga' already exists to avoid double migration
        check = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='t_familia_produtos' AND column_name='familia_carga'")).scalar()
        
        if check:
            print("Column 'familia_carga' already exists. Skipping rename.")
        else:
            print("Renaming 'familia' to 'familia_carga'...")
            db.execute(text("ALTER TABLE public.t_familia_produtos RENAME COLUMN familia TO familia_carga"))
            
        # 2. Check if new column 'familia' exists
        check_fam = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='t_familia_produtos' AND column_name='familia'")).scalar()
        
        if check_fam:
            print("Column 'familia' already exists. Skipping creation.")
        else:
            print("Adding new column 'familia'...")
            db.execute(text("ALTER TABLE public.t_familia_produtos ADD COLUMN familia TEXT"))
            
            print("Copying data from 'familia_carga' to 'familia'...")
            db.execute(text("UPDATE public.t_familia_produtos SET familia = familia_carga"))
        
        db.commit()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_familia()
