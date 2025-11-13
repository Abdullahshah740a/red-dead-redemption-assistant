from llm import LLAMA
import sqlite3
import os
from queue import Queue
import shutil # for deleting "audio_responses" folder, its used in delete_all_data()

DB_path = "chat_history.db"


# -----------------------
# Connection Pool Setup
# -----------------------
class ConnectionPool:
    def __init__(self, size=10):
        self.pool = Queue(maxsize=size)
        for _ in range(size):
            conn = sqlite3.connect(DB_path, check_same_thread=False) #Creates Database
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
       # Create sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_name TEXT
    )
    """)

    # Create history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        role TEXT,
        content TEXT,
        audio_path TEXT,   -- 🆕 new column for TTS file
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)
    conn.commit()
    pool.release_conn(conn)  # return connection back
    if not db_exists:
        print("✅ Database created: chat_history.db")
    else:
        print("ℹ️ Database loaded successfully.")


# Initialize DB
init_db()


def save_message(session_id, role, content,  audio_path=None):
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (session_id, role, content, audio_path) VALUES (?, ?, ?, ?)",
        (session_id, role, content, audio_path)
    )
    conn.commit()
    pool.release_conn(conn)



def load_history(session_id):
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, audio_path FROM history WHERE session_id=? ORDER BY id",
        (session_id,)
    )
    rows = cursor.fetchall()
    pool.release_conn(conn)
    return [{"role": role, "content": content, "audio_path": audio_path} for role, content, audio_path in rows]

def create_session(session_name="New Chat"):
    """Create a new chat session and return its unique session ID."""
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (session_name) VALUES (?)", (session_name,))
    session_id = cursor.lastrowid  # get the id of the new session (which will come at last row in table)
    conn.commit()
    pool.release_conn(conn)
    return session_id


# ---------------- Chat with LLM ----------------
def chat(session_id, system_message, user_message):
    """Chat with the LLM and save messages into history for a given session."""
    history = load_history(session_id)  
    recent_history = history[-10:]  # only last 10 messages
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
    messages.extend(recent_history)
    # save_message(session_id, "user", user_message)

    # get response from LLM
    response = LLAMA.invoke(messages).content
    # save_message(session_id, "assistant", response)

    return response



# Example usage
# response = chat("You are a helpful assistant.", "Hello, world!")
# print("Assistant:", response)

# Show chat history in terminal, good for testing purposes
print("\nChat history:")
for msg in load_history(1):   # example: session_id = 1
    print(f"{msg['role'].capitalize()}: {msg['content']}")
    

# ---------------- Generating Session name ----------------
def generate_session_name(user_message):
    """Generate a session name (3–5 words) from the first user message."""
    
    combined_prompt = f"""
    Generate a short and meaningful session name (3–5 words) 
    based on the following user message:
    
    "{user_message}"
    
    Return only the session name. No extra text or explanation.
    """
    
    # Ask the LLM to name the chat
    response = LLAMA.invoke([{"role": "user", "content": combined_prompt}])
    session_name = response.content.strip()
    
    # Clean up and handle edge cases
    session_name = session_name.strip('"').strip("'")
    if not session_name or len(session_name) > 50:
        words = user_message.split()[:4]
        session_name = " ".join(words) + "..."
    
    return session_name


# ---------------- Delete All Data ----------------
def delete_all_data():
    """Delete all chat data and the entire audio_responses folder."""
    conn = pool.get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    pool.release_conn(conn)

    audio_dir = "audio_responses"
    if os.path.exists(audio_dir):
        shutil.rmtree(audio_dir)  # delete the entire folder and its contents
    
    os.makedirs(audio_dir, exist_ok=True)  # recreate empty folder