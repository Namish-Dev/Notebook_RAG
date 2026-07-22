from database import conn, cursor

row=conn.execute("""SELECT title, section
FROM chunks
WHERE LOWER(section) LIKE '%projects%';""").fetchall()

print(row)