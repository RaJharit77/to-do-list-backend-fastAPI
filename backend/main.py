from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
from sqlite3 import connect, OperationalError
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware # type: ignore

app = FastAPI()

# Configuration CORS plus sécurisée
origins = [
    "https://to-do-list-task-app-lia.vercel.app",
    "https://to-do-list-task-app.onrender.com",
    "http://localhost:5173" 
]

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle Pydantic
class TodoItem(BaseModel):
    title: str
    completed: bool = False

# Connexion à la base de données
def get_db_connection():
    conn = connect('todos.db')
    conn.row_factory = lambda cursor, row: {
        'id': row[0],
        'title': row[1],
        'completed': bool(row[2]),
        'created_at': row[3]
    }
    return conn

# Initialiser la DB
@app.on_event("startup")
def init_db():
    try:
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except OperationalError as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

# Routes API
@app.get("/todos")
def get_todos():
    conn = get_db_connection()
    todos = conn.execute('SELECT * FROM todos ORDER BY created_at DESC').fetchall()
    conn.close()
    return todos

@app.post("/todos")
def create_todo(todo: TodoItem):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO todos (title, completed) VALUES (?, ?)',
        (todo.title, todo.completed)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {**todo.dict(), "id": new_id, "created_at": datetime.now()}

@app.patch("/todos/{todo_id}")
def update_todo(todo_id: int, todo: TodoItem):
    conn = get_db_connection()
    conn.execute(
        'UPDATE todos SET title = ?, completed = ? WHERE id = ?',
        (todo.title, todo.completed, todo_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Todo updated"}

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return {"message": "Todo deleted"}

@app.get("/health")
def health_check():
    return {"status": "ok"}