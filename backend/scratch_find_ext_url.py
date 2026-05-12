
import os
from sqlalchemy import create_engine, text

db_url = "postgresql://jdc:A2f2B5e6C2d9@dpg-cv20mptds78s73ba9gug-a.virginia-bethesda-dep.render.com/ordersync"
# Use a public engine if possible or just try again, maybe it was a transient error?
# Wait, I used the wrong hostname in the first attempt. 
# Render external host is usually dpg-xxx-a.virginia-postgres.render.com or similar.
# BUT wait, the connection string provided in the first run_command was:
# postgresql://jdc:A2f2B5e6C2d9@dpg-cv20mptds78s73ba9gug-a.virginia-bethesda-dep.render.com/ordersync
# That IS the internal one.

# I need the EXTERNAL one. 
# I'll check if I can find it in any file.
