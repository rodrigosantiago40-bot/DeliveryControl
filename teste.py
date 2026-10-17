import sqlite3
from datetime import datetime

conn = sqlite3.connect("delivery_control.db")
cursor = conn.cursor()

cursor.execute("SELECT id, numero_pedido, cliente, data, hora FROM pedidos")
rows = cursor.fetchall()

print(f"Total de pedidos salvos no banco: {len(rows)}")
for r in rows:
    print(f"Pedido #{r[1]} | Cliente: {r[2]} | Data no banco: '{r[3]}'")

print(f"Data de hoje no computador: {datetime.now().strftime('%d/%m/%Y')}")
conn.close()