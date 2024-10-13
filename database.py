import sqlite3

conn = sqlite3.connect('threads.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS threads (id INTEGER PRIMARY KEY, thread_id TEXT UNIQUE)''')
conn.commit()

def get_all_threads():
    cursor.execute("SELECT thread_id FROM threads")
    return cursor.fetchall()

def add_thread_to_db(thread_id):
    try:
        cursor.execute("INSERT INTO threads (thread_id) VALUES (?)", (thread_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_thread_from_db(thread_id):
    cursor.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
    conn.commit()