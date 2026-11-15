import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "search.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT
        );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lexicon (
            term_id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE NOT NULL
        );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inverted_index (
            term_id INTEGER NOT NULL,
            doc_id INTEGER NOT NULL,
            UNIQUE(term_id, doc_id)
        );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS links (
            from_doc_id INTEGER NOT NULL,
            to_doc_id INTEGER NOT NULL,
            UNIQUE(from_doc_id, to_doc_id)
        );
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pagerank (
            doc_id INTEGER PRIMARY KEY,
            score REAL NOT NULL
        );
    """
    )

    conn.commit()
    conn.close()


def upsert_document(doc_id, url, title=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO documents(doc_id, url, title) VALUES (?, ?, ?);",
        (doc_id, url, title),
    )
    if title:
        cur.execute("UPDATE documents SET title = ? WHERE doc_id = ?;", (title, doc_id))
    conn.commit()
    conn.close()


def get_or_create_term(term):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT term_id FROM lexicon WHERE term = ?;", (term,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]
    cur.execute("INSERT INTO lexicon(term) VALUES (?);", (term,))
    term_id = cur.lastrowid
    conn.commit()
    conn.close()
    return term_id


def add_inverted_entry(term_id, doc_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO inverted_index(term_id, doc_id) VALUES (?, ?);",
        (term_id, doc_id),
    )
    conn.commit()
    conn.close()


def insert_link(from_doc_id, to_doc_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO links(from_doc_id, to_doc_id) VALUES (?, ?);",
        (from_doc_id, to_doc_id),
    )
    conn.commit()
    conn.close()


def upsert_pagerank(doc_id, score):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO pagerank(doc_id, score) VALUES (?, ?);",
        (doc_id, score),
    )
    conn.commit()
    conn.close()


def query_by_term(term, limit=50):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT term_id FROM lexicon WHERE term = ?;", (term,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return []
    term_id = row[0]
    cur.execute(
        """
        SELECT d.url,
               COALESCE(d.title, d.url) AS title,
               COALESCE(p.score, 0.0) AS score
        FROM inverted_index ii
        JOIN documents d ON d.doc_id = ii.doc_id
        LEFT JOIN pagerank p ON p.doc_id = d.doc_id
        WHERE ii.term_id = ?
        ORDER BY score DESC
        LIMIT ?;
        """,
        (term_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_doc_ids():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT doc_id FROM documents;")
    ids = [r[0] for r in cur.fetchall()]
    conn.close()
    return ids


def get_all_links():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT from_doc_id, to_doc_id FROM links;")
    links = cur.fetchall()
    conn.close()
    return links
