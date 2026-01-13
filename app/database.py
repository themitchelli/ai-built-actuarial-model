"""
SQLite database for logging API executions.

Tracks all /api/parse and /api/project calls with:
- Timestamp, IP address, action type
- Tokens used, elapsed time
- Inputs and outputs
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# Database path
DB_PATH = Path(__file__).parent.parent / "activity.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                action_type TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                elapsed_ms REAL DEFAULT 0,
                input_data TEXT,
                output_data TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON executions(timestamp DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_type
            ON executions(action_type)
        """)


def log_execution(
    action_type: str,
    ip_address: Optional[str] = None,
    tokens_used: int = 0,
    elapsed_ms: float = 0,
    input_data: Optional[dict] = None,
    output_data: Optional[dict] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> str:
    """
    Log an API execution to the database.

    Returns the execution ID.
    """
    execution_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    with get_db() as conn:
        conn.execute("""
            INSERT INTO executions
            (id, timestamp, ip_address, action_type, tokens_used, elapsed_ms,
             input_data, output_data, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            timestamp,
            ip_address,
            action_type,
            tokens_used,
            elapsed_ms,
            json.dumps(input_data) if input_data else None,
            json.dumps(output_data) if output_data else None,
            1 if success else 0,
            error_message
        ))

    return execution_id


def get_all_executions(limit: int = 100, offset: int = 0) -> list[dict]:
    """Get all executions, most recent first."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id, timestamp, ip_address, action_type, tokens_used,
                   elapsed_ms, success, error_message
            FROM executions
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        return [dict(row) for row in cursor.fetchall()]


def get_execution_by_id(execution_id: str) -> Optional[dict]:
    """Get a single execution by ID with full details."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM executions WHERE id = ?
        """, (execution_id,))

        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            if result.get('input_data'):
                result['input_data'] = json.loads(result['input_data'])
            if result.get('output_data'):
                result['output_data'] = json.loads(result['output_data'])
            return result
        return None


def get_execution_count() -> int:
    """Get total number of executions."""
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM executions")
        return cursor.fetchone()[0]


def get_stats() -> dict:
    """Get summary statistics."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_executions,
                SUM(CASE WHEN action_type = 'parse' THEN 1 ELSE 0 END) as parse_count,
                SUM(CASE WHEN action_type = 'project' THEN 1 ELSE 0 END) as project_count,
                SUM(tokens_used) as total_tokens,
                AVG(elapsed_ms) as avg_elapsed_ms,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
            FROM executions
        """)
        row = cursor.fetchone()
        return dict(row) if row else {}


# Initialize database on module import
init_db()
