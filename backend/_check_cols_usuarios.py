import pg8000, os, re, ssl
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
m = re.match(r'postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(\w+)', DATABASE_URL)
ssl_ctx = ssl.create_default_context(); ssl_ctx.check_hostname = False; ssl_ctx.verify_mode = ssl.CERT_NONE
conn = pg8000.connect(host=m.group(3), port=int(m.group(4) or 5432), user=m.group(1), password=m.group(2), database=m.group(5), ssl_context=ssl_ctx)
cursor = conn.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'usuarios' ORDER BY ordinal_position")
for r in cursor.fetchall():
    print(r[0])
print("\n--- torneos_parejas ---")
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'torneos_parejas' ORDER BY ordinal_position")
for r in cursor.fetchall():
    print(r[0])
conn.close()
