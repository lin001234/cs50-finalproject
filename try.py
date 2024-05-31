
import sqlite3


conn = sqlite3.connect('app.db', timeout=10)
db = conn.cursor()
db.execute("SELECT * FROM focus WHERE user_id =3 AND hours = 0 AND minutes=30 AND date='2024-05-30'")
row = db.fetchall()
db.close()
conn.close()
print(row)

