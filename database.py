"""Render PostgreSQL bilan ishlash (psycopg2)."""
import logging
import random
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

import config

logger = logging.getLogger(__name__)

_pool = None


def get_conn():
    """PostgreSQL ulanishini qaytaradi."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.connect(config.DATABASE_URL)
        _pool.autocommit = True
    return _pool


@contextmanager
def get_cursor():
    """Cursor bilan ishlash uchun context manager."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        cur.close()
    except psycopg2.OperationalError:
        # Ulanish uzilgan bo'lsa, qayta ulanish
        global _pool
        _pool = None
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        cur.close()


def init_tables():
    """Jadvallarni yaratish (bot ishga tushganda chaqiriladi)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        language TEXT DEFAULT 'uz',
        is_subscribed BOOLEAN DEFAULT FALSE,
        is_blocked BOOLEAN DEFAULT FALSE,
        joined_at TIMESTAMPTZ DEFAULT NOW(),
        last_active TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        chat_id TEXT NOT NULL UNIQUE,
        title TEXT,
        invite_link TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS welcome_post (
        id SERIAL PRIMARY KEY,
        lang TEXT NOT NULL UNIQUE,
        text TEXT,
        photo_file_id TEXT,
        extra_button_text TEXT,
        extra_button_url TEXT,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS biography (
        id SERIAL PRIMARY KEY,
        lang TEXT NOT NULL UNIQUE,
        text TEXT,
        photo_file_id TEXT,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS works (
        id SERIAL PRIMARY KEY,
        type TEXT NOT NULL,
        lang TEXT NOT NULL DEFAULT 'uz',
        title TEXT NOT NULL,
        content TEXT,
        file_id TEXT,
        file_type TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS contests (
        id SERIAL PRIMARY KEY,
        lang TEXT NOT NULL DEFAULT 'uz',
        title TEXT NOT NULL,
        content TEXT,
        photo_file_id TEXT,
        link TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
        text TEXT NOT NULL,
        answer TEXT,
        is_answered BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        answered_at TIMESTAMPTZ
    );

    CREATE TABLE IF NOT EXISTS quotes (
        id SERIAL PRIMARY KEY,
        lang TEXT NOT NULL DEFAULT 'uz',
        text TEXT NOT NULL,
        source TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS quote_schedule (
        id SERIAL PRIMARY KEY,
        is_enabled BOOLEAN DEFAULT TRUE,
        interval_hours INT DEFAULT 24,
        send_time TEXT DEFAULT '09:00',
        last_sent_at TIMESTAMPTZ,
        last_quote_id INT,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_works_type_lang ON works(type, lang);
    CREATE INDEX IF NOT EXISTS idx_users_lang ON users(language);
    CREATE INDEX IF NOT EXISTS idx_questions_answered ON questions(is_answered);
    """)

    # quote_schedule jadvaliga boshlang'ich qator
    cur.execute("SELECT COUNT(*) FROM quote_schedule")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO quote_schedule (is_enabled, interval_hours, send_time) VALUES (TRUE, 24, '09:00')"
        )
    cur.close()
    logger.info("✅ Jadvallar tayyor.")


# ======================== USERS ========================
def upsert_user(user_id: int, username: str = None, full_name: str = None, language: str = None):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        exists = cur.fetchone()
        now = datetime.utcnow()
        if exists:
            if language:
                cur.execute(
                    "UPDATE users SET username=%s, full_name=%s, language=%s, last_active=%s WHERE id=%s",
                    (username, full_name, language, now, user_id),
                )
            else:
                cur.execute(
                    "UPDATE users SET username=%s, full_name=%s, last_active=%s WHERE id=%s",
                    (username, full_name, now, user_id),
                )
        else:
            cur.execute(
                "INSERT INTO users (id, username, full_name, language, joined_at, last_active) VALUES (%s,%s,%s,%s,%s,%s)",
                (user_id, username, full_name, language or config.DEFAULT_LANGUAGE, now, now),
            )


def get_user(user_id: int) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def set_user_language(user_id: int, lang: str):
    with get_cursor() as cur:
        cur.execute("UPDATE users SET language = %s WHERE id = %s", (lang, user_id))


def set_user_blocked(user_id: int, blocked: bool):
    with get_cursor() as cur:
        cur.execute("UPDATE users SET is_blocked = %s WHERE id = %s", (blocked, user_id))


def get_all_active_users() -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE is_blocked = FALSE")
        return cur.fetchall() or []


def count_users() -> dict:
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as c FROM users")
        total = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM users WHERE is_blocked = TRUE")
        blocked = cur.fetchone()["c"]
        return {"total": total, "blocked": blocked, "active": total - blocked}


# ======================== CHANNELS ========================
def get_channels(active_only: bool = True) -> list[dict]:
    with get_cursor() as cur:
        if active_only:
            cur.execute("SELECT * FROM channels WHERE is_active = TRUE")
        else:
            cur.execute("SELECT * FROM channels")
        return cur.fetchall() or []


def add_channel(chat_id: str, title: str = None, invite_link: str = None):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO channels (chat_id, title, invite_link, is_active)
               VALUES (%s, %s, %s, TRUE)
               ON CONFLICT (chat_id) DO UPDATE SET title=%s, invite_link=%s, is_active=TRUE""",
            (chat_id, title, invite_link, title, invite_link),
        )


def remove_channel(chat_id: str):
    with get_cursor() as cur:
        cur.execute("DELETE FROM channels WHERE chat_id = %s", (chat_id,))


# ======================== WELCOME POST ========================
def get_welcome(lang: str) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM welcome_post WHERE lang = %s", (lang,))
        return cur.fetchone()


def set_welcome(lang: str, text: str = None, photo_file_id: str = None,
                button_text: str = None, button_url: str = None):
    with get_cursor() as cur:
        now = datetime.utcnow()
        cur.execute(
            """INSERT INTO welcome_post (lang, text, photo_file_id, extra_button_text, extra_button_url, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (lang) DO UPDATE SET text=%s, photo_file_id=%s, extra_button_text=%s, extra_button_url=%s, updated_at=%s""",
            (lang, text, photo_file_id, button_text, button_url, now,
             text, photo_file_id, button_text, button_url, now),
        )


# ======================== BIOGRAPHY ========================
def get_biography(lang: str) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM biography WHERE lang = %s", (lang,))
        return cur.fetchone()


def set_biography(lang: str, text: str, photo_file_id: str = None):
    with get_cursor() as cur:
        now = datetime.utcnow()
        cur.execute(
            """INSERT INTO biography (lang, text, photo_file_id, updated_at)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (lang) DO UPDATE SET text=%s, photo_file_id=%s, updated_at=%s""",
            (lang, text, photo_file_id, now, text, photo_file_id, now),
        )


# ======================== WORKS ========================
def get_works_by_type(work_type: str, lang: str = "uz") -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM works WHERE type = %s AND lang = %s ORDER BY id", (work_type, lang))
        return cur.fetchall() or []


def count_works(lang: str = "uz") -> dict:
    out = {}
    with get_cursor() as cur:
        for t in ("asar", "hikoya", "sher"):
            cur.execute("SELECT COUNT(*) as c FROM works WHERE type = %s AND lang = %s", (t, lang))
            out[t] = cur.fetchone()["c"]
    return out


def get_work(work_id: int) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM works WHERE id = %s", (work_id,))
        return cur.fetchone()


def add_work(work_type: str, title: str, content: str = None,
             file_id: str = None, file_type: str = None, lang: str = "uz"):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO works (type, lang, title, content, file_id, file_type) VALUES (%s,%s,%s,%s,%s,%s)",
            (work_type, lang, title, content, file_id, file_type),
        )


def delete_work(work_id: int):
    with get_cursor() as cur:
        cur.execute("DELETE FROM works WHERE id = %s", (work_id,))


# ======================== CONTESTS ========================
def get_contests(lang: str = "uz") -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM contests WHERE lang = %s ORDER BY id DESC", (lang,))
        return cur.fetchall() or []


def get_contest(contest_id: int) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM contests WHERE id = %s", (contest_id,))
        return cur.fetchone()


def add_contest(title: str, content: str, photo_file_id: str = None,
                link: str = None, lang: str = "uz"):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO contests (lang, title, content, photo_file_id, link) VALUES (%s,%s,%s,%s,%s)",
            (lang, title, content, photo_file_id, link),
        )


def delete_contest(contest_id: int):
    with get_cursor() as cur:
        cur.execute("DELETE FROM contests WHERE id = %s", (contest_id,))


# ======================== QUESTIONS ========================
def add_question(user_id: int, text: str) -> int:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO questions (user_id, text) VALUES (%s, %s) RETURNING id",
            (user_id, text),
        )
        row = cur.fetchone()
        return row["id"] if row else 0


def get_unanswered_questions() -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM questions WHERE is_answered = FALSE ORDER BY id")
        return cur.fetchall() or []


def answer_question(qid: int, answer: str):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE questions SET answer=%s, is_answered=TRUE, answered_at=%s WHERE id=%s",
            (answer, datetime.utcnow(), qid),
        )


def get_question(qid: int) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM questions WHERE id = %s", (qid,))
        return cur.fetchone()


# ======================== QUOTES ========================
def get_all_quotes(lang: str = "uz") -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM quotes WHERE lang = %s", (lang,))
        return cur.fetchall() or []


def add_quote(text: str, source: str = None, lang: str = "uz"):
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO quotes (lang, text, source) VALUES (%s, %s, %s)",
            (lang, text, source),
        )


def delete_quote(quote_id: int):
    with get_cursor() as cur:
        cur.execute("DELETE FROM quotes WHERE id = %s", (quote_id,))


def get_random_quote(lang: str = "uz", exclude_id: int = None) -> Optional[dict]:
    quotes = get_all_quotes(lang)
    if exclude_id:
        quotes = [q for q in quotes if q["id"] != exclude_id]
    return random.choice(quotes) if quotes else None


# ======================== QUOTE SCHEDULE ========================
def get_schedule() -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM quote_schedule LIMIT 1")
        return cur.fetchone()


def update_schedule(is_enabled: bool = None, interval_hours: int = None,
                    send_time: str = None, last_quote_id: int = None):
    sched = get_schedule()
    if not sched:
        return
    now = datetime.utcnow()
    with get_cursor() as cur:
        if is_enabled is not None:
            cur.execute("UPDATE quote_schedule SET is_enabled=%s, updated_at=%s WHERE id=%s",
                        (is_enabled, now, sched["id"]))
        if interval_hours is not None:
            cur.execute("UPDATE quote_schedule SET interval_hours=%s, updated_at=%s WHERE id=%s",
                        (interval_hours, now, sched["id"]))
        if send_time is not None:
            cur.execute("UPDATE quote_schedule SET send_time=%s, updated_at=%s WHERE id=%s",
                        (send_time, now, sched["id"]))
        if last_quote_id is not None:
            cur.execute("UPDATE quote_schedule SET last_quote_id=%s, last_sent_at=%s, updated_at=%s WHERE id=%s",
                        (last_quote_id, now, now, sched["id"]))
