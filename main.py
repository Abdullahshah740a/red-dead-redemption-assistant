from llm import LLAMA
import sqlite3
import os
from queue import Queue

DB_path = "chat_history.db"


# -----------------------
# Connection Pool Setup
# -----------------------
class ConnectionPool:
    def __init__(self, size=10):
        self.pool = Queue(maxsize=size)
        for _ in range(size):
            conn = sqlite3.connect(DB_path, check_same_thread=False)
            self.pool.put(conn)

    def get_conn(self):
        return self.pool.get()

    def release_conn(self, conn):
        self.pool.put(conn)


# Initialize pool (10 connections ready)
pool = ConnectionPool(size=10)

# <---------------------->

def init_db():
    """Initialize the SQLite database and create history table if not exists."""
    db_exists = os.path.exists(DB_path)
    conn = pool.get_conn()
    cursor = conn.cursor()
    query1 = """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        content TEXT
    )
    """
    cursor.execute(query1)
    conn.commit()
    pool.release_conn(conn)  # return connection back
    if not db_exists:
        print("✅ Database created: chat_history.db")
    else:
        print("ℹ️ Database loaded successfully.")


# Initialize DB
init_db()


def save_message(role, content):
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    pool.release_conn(conn)


def load_history():
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM history ORDER BY id")
    rows = cursor.fetchall()
    pool.release_conn(conn)
    return [{"role": role, "content": content} for role, content in rows]


def chat(system_message, user_message):
    """Chat with the LLM and save messages into history."""
    history = load_history()
    recent_history = history[-20:]
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    messages.extend(recent_history)
    # save_message("user", user_message)
    response = LLAMA.invoke(messages).content
    # save_message("assistant", response)  # also save AI reply
    return response


# Example usage
# response = chat("You are a helpful assistant.", "Hello, world!")
# print("Assistant:", response)

# Show chat history
print("\nChat history:")
for msg in load_history():
    print(f"{msg['role'].capitalize()}: {msg['content']}")
