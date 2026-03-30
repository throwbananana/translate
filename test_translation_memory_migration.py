import sqlite3
import tempfile
import unittest
from pathlib import Path

from translation_memory import TranslationMemory


def _create_legacy_db(path: Path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_hash TEXT NOT NULL,
            source_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            source_lang TEXT DEFAULT '',
            target_lang TEXT NOT NULL,
            api_provider TEXT DEFAULT '',
            model TEXT DEFAULT '',
            quality_score INTEGER DEFAULT 0,
            use_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_hash, target_lang)
        )
        """
    )
    conn.execute("CREATE INDEX idx_source_hash ON memories(source_hash)")
    conn.execute("CREATE INDEX idx_target_lang ON memories(target_lang)")
    conn.execute("CREATE INDEX idx_updated_at ON memories(updated_at)")
    conn.execute(
        """
        CREATE TABLE stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            lookups INTEGER DEFAULT 0,
            hits INTEGER DEFAULT 0,
            misses INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        INSERT INTO memories (
            source_hash, source_text, translated_text, source_lang,
            target_lang, api_provider, model, quality_score, use_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "legacy-hash-1",
            "legacy text",
            "遗留文本",
            "en",
            "中文",
            "test",
            "legacy-model",
            0,
            1,
        ),
    )
    conn.commit()
    conn.close()


class TranslationMemoryMigrationTests(unittest.TestCase):
    def test_translation_memory_migrates_legacy_repo_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            legacy_db = tmp_path / "translation_memory.db"
            runtime_db = tmp_path / "runtime" / "translation_memory.db"
            _create_legacy_db(legacy_db)

            tm = TranslationMemory(db_path=str(runtime_db), legacy_db_path=str(legacy_db))
            try:
                self.assertTrue(runtime_db.exists())
                self.assertEqual(tm.lookup("legacy text", "中文"), "遗留文本")
            finally:
                tm.close()

    def test_translation_memory_prefers_existing_runtime_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            legacy_db = tmp_path / "translation_memory.db"
            runtime_db = tmp_path / "runtime" / "translation_memory.db"
            runtime_db.parent.mkdir(parents=True, exist_ok=True)
            _create_legacy_db(legacy_db)
            _create_legacy_db(runtime_db)

            tm = TranslationMemory(db_path=str(runtime_db), legacy_db_path=str(legacy_db))
            try:
                self.assertEqual(tm.lookup("legacy text", "中文"), "遗留文本")
                self.assertTrue(runtime_db.exists())
            finally:
                tm.close()


if __name__ == "__main__":
    unittest.main()
