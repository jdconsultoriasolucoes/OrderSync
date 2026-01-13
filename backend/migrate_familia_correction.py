import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_familia_correction():
    # Database connection
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set in env, using fallback")
        db_url = "postgresql://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

    engine = create_engine(db_url)
    db = engine.connect()

    try:
        print("Starting migration: t_familia_produtos column rename/swap...")
        # Current state:
        # - familia: CLEAN
        # - familia_carga: RAW

        # Desired state:
        # - marca: CLEAN
        # - familia: RAW

        # 1. Check if 'marca' column exists in t_familia_produtos
        check_marca = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='t_familia_produtos' AND column_name='marca'")).scalar()
        
        if not check_marca:
            print("Renaming 'familia' (clean) to 'marca'...")
            # We assume 'familia' is currently the clean one.
            db.execute(text("ALTER TABLE public.t_familia_produtos RENAME COLUMN familia TO marca"))
        else:
            print("Column 'marca' already exists. Skipping rename.")

        # 2. Check if 'familia_carga' exists and needs renaming to 'familia'
        # Note: if we just renamed 'familia' to 'marca', the name 'familia' is now free.
        
        check_fam_carga = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='t_familia_produtos' AND column_name='familia_carga'")).scalar()
        
        if check_fam_carga:
            print("Renaming 'familia_carga' (raw) to 'familia'...")
            try:
                 db.execute(text("ALTER TABLE public.t_familia_produtos RENAME COLUMN familia_carga TO familia"))
            except Exception as e:
                # If 'familia' already exists (maybe from a partial run or confusion), this will fail.
                # In that case, we might need to handle it, but simple rename should work if previous step freed the name.
                print(f"Error renaming familia_carga: {e}")
                raise e
        else:
             print("Column 'familia_carga' not found. It might have consistently been renamed already.")

        db.commit()
        print("Migration schema correction completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_familia_correction()
