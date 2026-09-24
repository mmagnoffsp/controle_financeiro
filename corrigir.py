import sqlite3
conn = sqlite3.connect("financeiro.db")
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE lancamentos ADD COLUMN status TEXT DEFAULT 'Oficial'")
    print("✅ Coluna adicionada!")
except Exception as e:
    print("ℹ️", e)
conn.commit()
conn.close()
print("🏁 Pronto!")
