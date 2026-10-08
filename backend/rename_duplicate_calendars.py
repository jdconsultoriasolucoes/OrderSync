import sys
import os

os.environ["DATABASE_URL"] = "postgresql+psycopg2://dispet_admin_:VTCgwlOp1saQYLdv2gLeHQOVdbhvZO33@dpg-d4781ehr0fns73f9ipc0-a.oregon-postgres.render.com/db_ordersync"

# Add the backend directory to sys.path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.calendario import CalendarModel
from models.usuario import UsuarioModel
from models.perfil import PerfilModel

def rename_duplicates():
    db = SessionLocal()
    try:
        # Group calendars by user_id and name
        calendars = db.query(CalendarModel).order_by(CalendarModel.user_id, CalendarModel.name).all()
        
        seen = {}
        for cal in calendars:
            key = (cal.user_id, cal.name)
            if key not in seen:
                seen[key] = 1
            else:
                new_name = f"{cal.name}_{seen[key]}"
                cal.name = new_name
                seen[key] += 1
                db.add(cal)
                print(f"Renamed to {new_name}")
        db.commit()
        print("Duplicates renamed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    rename_duplicates()
