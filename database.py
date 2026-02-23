import sqlite3
import os
from datetime import datetime, timedelta


DB_PATH = os.path.join(os.path.dirname(__file__), "news_history.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            summary TEXT,
            published_date TEXT,
            collected_at TEXT NOT NULL,
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def article_exists(url):
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None


def save_article(source, title, url, summary="", published_date=""):
    if article_exists(url):
        return False
    conn = get_connection()
    conn.execute(
        "INSERT INTO articles (source, title, url, summary, published_date, collected_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (source, title, url, summary, published_date, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return True


def get_unsent_articles():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM articles WHERE sent = 0 ORDER BY published_date DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_as_sent(article_ids):
    if not article_ids:
        return
    conn = get_connection()
    placeholders = ",".join("?" for _ in article_ids)
    conn.execute(f"UPDATE articles SET sent = 1 WHERE id IN ({placeholders})", article_ids)
    conn.commit()
    conn.close()


def cleanup_old_articles(days=400):
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    conn = get_connection()
    conn.execute("DELETE FROM articles WHERE collected_at < ?", (cutoff,))
    conn.commit()
    conn.close()
