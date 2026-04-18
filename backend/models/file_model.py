import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "contracts.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            contract_type TEXT,
            status TEXT DEFAULT 'temp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            contract_type TEXT,
            stance TEXT,
            result_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES contract_files(id)
        )
    """)

    conn.commit()
    conn.close()


def create_file(file_name: str, file_path: str, file_size: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contract_files (file_name, file_path, file_size, status) VALUES (?, ?, ?, 'temp')",
        (file_name, file_path, file_size)
    )
    conn.commit()
    file_id = cursor.lastrowid
    conn.close()
    return file_id


def get_file(file_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contract_files WHERE id = ?", (file_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_file_status(file_id: int, status: str, contract_type: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    if contract_type:
        cursor.execute(
            "UPDATE contract_files SET status = ?, contract_type = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, contract_type, file_id)
        )
    else:
        cursor.execute(
            "UPDATE contract_files SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, file_id)
        )
    conn.commit()
    conn.close()


def delete_file(file_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM contract_files WHERE id = ?", (file_id,))
    row = cursor.fetchone()

    if row:
        file_path = row["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        cursor.execute("DELETE FROM contract_files WHERE id = ?", (file_id,))

    conn.commit()
    conn.close()


def save_result(file_id: int, contract_type: str, stance: str, result_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contract_results (file_id, contract_type, stance, result_data) VALUES (?, ?, ?, ?)",
        (file_id, contract_type, stance, json.dumps(result_data, ensure_ascii=False))
    )
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    return result_id


def get_result(result_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contract_results WHERE id = ?", (result_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("result_data"):
            d["result_data"] = json.loads(d["result_data"])
        return d
    return None


def cleanup_temp_files():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contract_files WHERE status = 'temp'")
    rows = cursor.fetchall()

    for row in rows:
        file_path = row["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        cursor.execute("DELETE FROM contract_files WHERE id = ?", (row["id"],))

    conn.commit()
    conn.close()


def get_saved_contracts(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cf.id, cf.file_name, cf.created_at,
               COALESCE(cr.contract_type, cf.contract_type) as contract_type,
               cr.stance, cr.result_data
        FROM contract_files cf
        LEFT JOIN contract_results cr ON cf.id = cr.file_id
        WHERE cf.status = 'saved'
        ORDER BY cf.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        if d.get("result_data"):
            try:
                d["result_data"] = json.loads(d["result_data"])
            except:
                pass
        results.append(d)
    return results


def get_all_saved_contracts():
    return get_saved_contracts(limit=100)
