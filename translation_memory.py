#! python
# -*- coding: utf-8 -*-
"""
翻译记忆 (Translation Memory) 模块
使用 SQLite 存储翻译历史，避免重复翻译相同内容，节省 API 费用

功能：
- 基于文本哈希的快速查找
- 支持模糊匹配（相似度查找）
- 自动清理过期记录
- 统计信息和导出功能
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import difflib


class TranslationMemory:
    """翻译记忆管理器"""

    def __init__(self, db_path: str = None):
        """
        初始化翻译记忆数据库

        Args:
            db_path: 数据库文件路径，默认在程序目录下的 translation_memory.db
        """
        if db_path is None:
            db_path = Path(__file__).parent / 'translation_memory.db'

        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        cursor = self.conn.cursor()

        # 主表：存储翻译记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
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
        ''')

        # 索引：加速查询
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source_hash
            ON memories(source_hash)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_target_lang
            ON memories(target_lang)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_updated_at
            ON memories(updated_at)
        ''')

        # 统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                lookups INTEGER DEFAULT 0,
                hits INTEGER DEFAULT 0,
                misses INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0
            )
        ''')

        self.conn.commit()

    def _compute_hash(self, text: str, target_lang: str) -> str:
        """
        计算文本的哈希值

        Args:
            text: 源文本
            target_lang: 目标语言

        Returns:
            MD5 哈希字符串
        """
        # 标准化文本：去除首尾空白，统一换行符
        normalized = text.strip().replace('\r\n', '\n').replace('\r', '\n')
        key = f"{normalized}:::{target_lang}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def _update_stats(self, stat_type: str):
        """更新统计信息"""
        today = datetime.now().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO stats (date, lookups, hits, misses, saves)
            VALUES (?, 0, 0, 0, 0)
            ON CONFLICT(date) DO NOTHING
        ''', (today,))

        if stat_type == 'lookup':
            cursor.execute('UPDATE stats SET lookups = lookups + 1 WHERE date = ?', (today,))
        elif stat_type == 'hit':
            cursor.execute('UPDATE stats SET hits = hits + 1 WHERE date = ?', (today,))
        elif stat_type == 'miss':
            cursor.execute('UPDATE stats SET misses = misses + 1 WHERE date = ?', (today,))
        elif stat_type == 'save':
            cursor.execute('UPDATE stats SET saves = saves + 1 WHERE date = ?', (today,))

        self.conn.commit()

    def lookup(self, text: str, target_lang: str) -> Optional[str]:
        """
        查找翻译记忆

        Args:
            text: 源文本
            target_lang: 目标语言

        Returns:
            已存储的翻译结果，如果没找到返回 None
        """
        self._update_stats('lookup')

        source_hash = self._compute_hash(text, target_lang)
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT translated_text, use_count FROM memories
            WHERE source_hash = ? AND target_lang = ?
        ''', (source_hash, target_lang))

        result = cursor.fetchone()

        if result:
            self._update_stats('hit')
            # 更新使用次数
            cursor.execute('''
                UPDATE memories
                SET use_count = use_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE source_hash = ? AND target_lang = ?
            ''', (source_hash, target_lang))
            self.conn.commit()
            return result['translated_text']

        self._update_stats('miss')
        return None

    def lookup_similar(self, text: str, target_lang: str,
                       threshold: float = 0.85) -> List[Dict]:
        """
        模糊查找相似的翻译记忆

        Args:
            text: 源文本
            target_lang: 目标语言
            threshold: 相似度阈值 (0.0-1.0)

        Returns:
            相似翻译列表，包含源文本、翻译、相似度
        """
        cursor = self.conn.cursor()

        # 获取同目标语言的所有记录（限制数量避免性能问题）
        cursor.execute('''
            SELECT source_text, translated_text, use_count
            FROM memories
            WHERE target_lang = ?
            ORDER BY use_count DESC, updated_at DESC
            LIMIT 1000
        ''', (target_lang,))

        results = []
        normalized_text = text.strip()

        for row in cursor.fetchall():
            similarity = difflib.SequenceMatcher(
                None, normalized_text, row['source_text']
            ).ratio()

            if similarity >= threshold:
                results.append({
                    'source': row['source_text'],
                    'translated': row['translated_text'],
                    'similarity': round(similarity, 3),
                    'use_count': row['use_count']
                })

        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:10]  # 最多返回10个结果

    def store(self, source_text: str, translated_text: str, target_lang: str,
              source_lang: str = '', api_provider: str = '', model: str = '',
              quality_score: int = 0) -> bool:
        """
        存储翻译记忆

        Args:
            source_text: 源文本
            translated_text: 翻译结果
            target_lang: 目标语言
            source_lang: 源语言（可选）
            api_provider: API 提供商（可选）
            model: 模型名称（可选）
            quality_score: 质量评分 0-100（可选）

        Returns:
            是否存储成功
        """
        if not source_text or not translated_text or not target_lang:
            return False

        source_hash = self._compute_hash(source_text, target_lang)

        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO memories
                (source_hash, source_text, translated_text, source_lang,
                 target_lang, api_provider, model, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_hash, target_lang) DO UPDATE SET
                    translated_text = excluded.translated_text,
                    api_provider = excluded.api_provider,
                    model = excluded.model,
                    quality_score = excluded.quality_score,
                    use_count = use_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            ''', (source_hash, source_text.strip(), translated_text.strip(),
                  source_lang, target_lang, api_provider, model, quality_score))

            self.conn.commit()
            self._update_stats('save')
            return True

        except Exception as e:
            print(f"存储翻译记忆失败: {e}")
            return False

    def delete(self, source_text: str, target_lang: str) -> bool:
        """删除指定的翻译记忆"""
        source_hash = self._compute_hash(source_text, target_lang)
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM memories WHERE source_hash = ? AND target_lang = ?
        ''', (source_hash, target_lang))
        self.conn.commit()
        return cursor.rowcount > 0

    def cleanup(self, days: int = 90, min_use_count: int = 1) -> int:
        """
        清理过期或低使用率的记录

        Args:
            days: 超过多少天未使用的记录将被删除
            min_use_count: 使用次数低于此值的记录将被删除

        Returns:
            删除的记录数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor = self.conn.cursor()

        cursor.execute('''
            DELETE FROM memories
            WHERE updated_at < ? AND use_count < ?
        ''', (cutoff_date.isoformat(), min_use_count))

        deleted = cursor.rowcount
        self.conn.commit()

        # 整理数据库
        cursor.execute('VACUUM')

        return deleted

    def get_stats(self) -> Dict:
        """
        获取翻译记忆统计信息

        Returns:
            统计信息字典
        """
        cursor = self.conn.cursor()

        # 总记录数
        cursor.execute('SELECT COUNT(*) as total FROM memories')
        total_records = cursor.fetchone()['total']

        # 按目标语言分组
        cursor.execute('''
            SELECT target_lang, COUNT(*) as count
            FROM memories
            GROUP BY target_lang
        ''')
        by_language = {row['target_lang']: row['count'] for row in cursor.fetchall()}

        # 按 API 提供商分组
        cursor.execute('''
            SELECT api_provider, COUNT(*) as count
            FROM memories
            WHERE api_provider != ''
            GROUP BY api_provider
        ''')
        by_provider = {row['api_provider']: row['count'] for row in cursor.fetchall()}

        # 最近7天的命中率
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT SUM(lookups) as lookups, SUM(hits) as hits
            FROM stats
            WHERE date >= ?
        ''', (week_ago,))

        row = cursor.fetchone()
        lookups = row['lookups'] or 0
        hits = row['hits'] or 0
        hit_rate = (hits / lookups * 100) if lookups > 0 else 0

        # 数据库大小
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return {
            'total_records': total_records,
            'by_language': by_language,
            'by_provider': by_provider,
            'weekly_lookups': lookups,
            'weekly_hits': hits,
            'weekly_hit_rate': round(hit_rate, 1),
            'db_size_bytes': db_size,
            'db_size_mb': round(db_size / 1024 / 1024, 2)
        }

    def export_to_json(self, output_path: str, target_lang: str = None) -> int:
        """
        导出翻译记忆到 JSON 文件

        Args:
            output_path: 输出文件路径
            target_lang: 只导出指定目标语言的记录（可选）

        Returns:
            导出的记录数
        """
        cursor = self.conn.cursor()

        if target_lang:
            cursor.execute('''
                SELECT source_text, translated_text, source_lang, target_lang,
                       api_provider, model, quality_score, use_count, created_at
                FROM memories
                WHERE target_lang = ?
                ORDER BY use_count DESC
            ''', (target_lang,))
        else:
            cursor.execute('''
                SELECT source_text, translated_text, source_lang, target_lang,
                       api_provider, model, quality_score, use_count, created_at
                FROM memories
                ORDER BY target_lang, use_count DESC
            ''')

        records = [dict(row) for row in cursor.fetchall()]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        return len(records)

    def import_from_json(self, input_path: str) -> Tuple[int, int]:
        """
        从 JSON 文件导入翻译记忆

        Args:
            input_path: 输入文件路径

        Returns:
            (成功导入数, 跳过数) 元组
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            records = json.load(f)

        imported = 0
        skipped = 0

        for record in records:
            if self.store(
                source_text=record.get('source_text', ''),
                translated_text=record.get('translated_text', ''),
                target_lang=record.get('target_lang', ''),
                source_lang=record.get('source_lang', ''),
                api_provider=record.get('api_provider', ''),
                model=record.get('model', ''),
                quality_score=record.get('quality_score', 0)
            ):
                imported += 1
            else:
                skipped += 1

        return imported, skipped

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 全局实例（方便导入使用）
_default_tm = None

def get_translation_memory() -> TranslationMemory:
    """获取默认的翻译记忆实例"""
    global _default_tm
    if _default_tm is None:
        _default_tm = TranslationMemory()
    return _default_tm


if __name__ == '__main__':
    # 测试代码
    print("翻译记忆模块测试")
    print("=" * 50)

    tm = TranslationMemory()

    # 测试存储
    tm.store("Hello, world!", "你好，世界！", "中文", api_provider="test")
    tm.store("Good morning", "早上好", "中文", api_provider="test")
    tm.store("Thank you", "谢谢", "中文", api_provider="test")

    # 测试查找
    result = tm.lookup("Hello, world!", "中文")
    print(f"查找 'Hello, world!' -> {result}")

    # 测试模糊查找
    similar = tm.lookup_similar("Hello world", "中文", threshold=0.7)
    print(f"模糊查找 'Hello world' -> {similar}")

    # 统计信息
    stats = tm.get_stats()
    print(f"\n统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")

    tm.close()
    print("\n测试完成!")
