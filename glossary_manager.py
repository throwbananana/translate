#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
术语表管理 (Glossary Manager) 模块
管理专业术语的翻译一致性

功能：
- 术语表的增删改查
- 支持多个术语表（按领域分类）
- 自动在翻译提示词中注入术语
- 导入导出功能（JSON/CSV/Excel）
"""

import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class GlossaryManager:
    """术语表管理器"""

    def __init__(self, glossary_dir: str = None):
        """
        初始化术语表管理器

        Args:
            glossary_dir: 术语表存储目录，默认在程序目录下的 glossaries/
        """
        if glossary_dir is None:
            glossary_dir = Path(__file__).parent / 'glossaries'

        self.glossary_dir = Path(glossary_dir)
        self.glossary_dir.mkdir(exist_ok=True)

        # 当前活动的术语表
        self.active_glossaries: Dict[str, Dict] = {}

        # 加载默认术语表
        self._load_default_glossaries()

    def _load_default_glossaries(self):
        """加载默认术语表"""
        default_file = self.glossary_dir / 'default.json'
        if default_file.exists():
            self.load_glossary('default')

    def _get_glossary_path(self, name: str) -> Path:
        """获取术语表文件路径"""
        return self.glossary_dir / f'{name}.json'

    def create_glossary(self, name: str, description: str = '',
                       source_lang: str = '', target_lang: str = '') -> bool:
        """
        创建新的术语表

        Args:
            name: 术语表名称
            description: 描述
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            是否创建成功
        """
        path = self._get_glossary_path(name)
        if path.exists():
            return False

        glossary = {
            'name': name,
            'description': description,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'terms': {}
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(glossary, f, ensure_ascii=False, indent=2)

        return True

    def load_glossary(self, name: str) -> bool:
        """
        加载术语表到内存

        Args:
            name: 术语表名称

        Returns:
            是否加载成功
        """
        path = self._get_glossary_path(name)
        if not path.exists():
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                glossary = json.load(f)
            self.active_glossaries[name] = glossary
            return True
        except Exception as e:
            print(f"加载术语表 '{name}' 失败: {e}")
            return False

    def unload_glossary(self, name: str):
        """从内存中卸载术语表"""
        if name in self.active_glossaries:
            del self.active_glossaries[name]

    def save_glossary(self, name: str) -> bool:
        """
        保存术语表到文件

        Args:
            name: 术语表名称

        Returns:
            是否保存成功
        """
        if name not in self.active_glossaries:
            return False

        path = self._get_glossary_path(name)
        glossary = self.active_glossaries[name]
        glossary['updated_at'] = datetime.now().isoformat()

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(glossary, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存术语表 '{name}' 失败: {e}")
            return False

    def delete_glossary(self, name: str) -> bool:
        """删除术语表"""
        self.unload_glossary(name)
        path = self._get_glossary_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_glossaries(self) -> List[Dict]:
        """
        列出所有可用的术语表

        Returns:
            术语表信息列表
        """
        glossaries = []
        for path in self.glossary_dir.glob('*.json'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                glossaries.append({
                    'name': data.get('name', path.stem),
                    'description': data.get('description', ''),
                    'source_lang': data.get('source_lang', ''),
                    'target_lang': data.get('target_lang', ''),
                    'term_count': len(data.get('terms', {})),
                    'updated_at': data.get('updated_at', ''),
                    'is_active': path.stem in self.active_glossaries
                })
            except:
                continue

        return glossaries

    def add_term(self, glossary_name: str, source: str, target: str,
                 notes: str = '', category: str = '') -> bool:
        """
        添加术语

        Args:
            glossary_name: 术语表名称
            source: 源术语
            target: 目标翻译
            notes: 备注
            category: 分类

        Returns:
            是否添加成功
        """
        if glossary_name not in self.active_glossaries:
            if not self.load_glossary(glossary_name):
                # 如果不存在，创建新的
                self.create_glossary(glossary_name)
                self.load_glossary(glossary_name)

        glossary = self.active_glossaries[glossary_name]
        glossary['terms'][source] = {
            'target': target,
            'notes': notes,
            'category': category,
            'added_at': datetime.now().isoformat()
        }

        return self.save_glossary(glossary_name)

    def remove_term(self, glossary_name: str, source: str) -> bool:
        """删除术语"""
        if glossary_name not in self.active_glossaries:
            return False

        glossary = self.active_glossaries[glossary_name]
        if source in glossary['terms']:
            del glossary['terms'][source]
            return self.save_glossary(glossary_name)

        return False

    def update_term(self, glossary_name: str, source: str,
                    target: str = None, notes: str = None,
                    category: str = None) -> bool:
        """更新术语"""
        if glossary_name not in self.active_glossaries:
            return False

        glossary = self.active_glossaries[glossary_name]
        if source not in glossary['terms']:
            return False

        term = glossary['terms'][source]
        if target is not None:
            term['target'] = target
        if notes is not None:
            term['notes'] = notes
        if category is not None:
            term['category'] = category
        term['updated_at'] = datetime.now().isoformat()

        return self.save_glossary(glossary_name)

    def get_term(self, source: str, glossary_name: str = None) -> Optional[Dict]:
        """
        查找术语

        Args:
            source: 源术语
            glossary_name: 指定术语表（可选，不指定则搜索所有活动术语表）

        Returns:
            术语信息字典或 None
        """
        if glossary_name:
            if glossary_name in self.active_glossaries:
                terms = self.active_glossaries[glossary_name].get('terms', {})
                if source in terms:
                    return {'glossary': glossary_name, **terms[source]}
        else:
            # 搜索所有活动术语表
            for name, glossary in self.active_glossaries.items():
                terms = glossary.get('terms', {})
                if source in terms:
                    return {'glossary': name, **terms[source]}

        return None

    def search_terms(self, query: str, glossary_name: str = None) -> List[Dict]:
        """
        搜索术语（支持模糊匹配）

        Args:
            query: 搜索关键词
            glossary_name: 指定术语表（可选）

        Returns:
            匹配的术语列表
        """
        results = []
        query_lower = query.lower()

        glossaries = {glossary_name: self.active_glossaries[glossary_name]} \
            if glossary_name and glossary_name in self.active_glossaries \
            else self.active_glossaries

        for name, glossary in glossaries.items():
            for source, info in glossary.get('terms', {}).items():
                if (query_lower in source.lower() or
                    query_lower in info.get('target', '').lower() or
                    query_lower in info.get('notes', '').lower()):
                    results.append({
                        'glossary': name,
                        'source': source,
                        **info
                    })

        return results

    def find_terms_in_text(self, text: str) -> List[Dict]:
        """
        在文本中查找所有匹配的术语

        Args:
            text: 要检查的文本

        Returns:
            在文本中找到的术语列表
        """
        found = []

        for name, glossary in self.active_glossaries.items():
            for source, info in glossary.get('terms', {}).items():
                if source in text:
                    found.append({
                        'glossary': name,
                        'source': source,
                        'target': info.get('target', ''),
                        'notes': info.get('notes', ''),
                        'position': text.find(source)
                    })

        # 按在文本中出现的位置排序
        found.sort(key=lambda x: x['position'])
        return found

    def generate_prompt_injection(self, text: str, max_terms: int = 20) -> str:
        """
        生成用于注入到翻译提示词的术语说明

        Args:
            text: 要翻译的文本
            max_terms: 最多包含多少个术语

        Returns:
            术语说明字符串
        """
        found_terms = self.find_terms_in_text(text)

        if not found_terms:
            return ""

        # 去重并限制数量
        seen = set()
        unique_terms = []
        for term in found_terms:
            if term['source'] not in seen:
                seen.add(term['source'])
                unique_terms.append(term)
                if len(unique_terms) >= max_terms:
                    break

        if not unique_terms:
            return ""

        # 生成术语说明
        lines = ["请在翻译时使用以下术语："]
        for term in unique_terms:
            line = f"- \"{term['source']}\" → \"{term['target']}\""
            if term.get('notes'):
                line += f" ({term['notes']})"
            lines.append(line)

        return "\n".join(lines) + "\n\n"

    def export_to_csv(self, glossary_name: str, output_path: str) -> int:
        """
        导出术语表到 CSV 文件

        Args:
            glossary_name: 术语表名称
            output_path: 输出文件路径

        Returns:
            导出的术语数
        """
        if glossary_name not in self.active_glossaries:
            if not self.load_glossary(glossary_name):
                return 0

        glossary = self.active_glossaries[glossary_name]
        terms = glossary.get('terms', {})

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['源术语', '目标翻译', '分类', '备注'])

            for source, info in terms.items():
                writer.writerow([
                    source,
                    info.get('target', ''),
                    info.get('category', ''),
                    info.get('notes', '')
                ])

        return len(terms)

    def import_from_csv(self, glossary_name: str, input_path: str) -> Tuple[int, int]:
        """
        从 CSV 文件导入术语

        Args:
            glossary_name: 术语表名称
            input_path: 输入文件路径

        Returns:
            (成功导入数, 跳过数) 元组
        """
        imported = 0
        skipped = 0

        # 确保术语表存在
        if glossary_name not in self.active_glossaries:
            if not self.load_glossary(glossary_name):
                self.create_glossary(glossary_name)
                self.load_glossary(glossary_name)

        # 尝试多种编码
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030']
        content = None

        for encoding in encodings:
            try:
                with open(input_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ValueError("无法识别文件编码")

        # 解析 CSV
        lines = content.strip().split('\n')
        reader = csv.reader(lines)

        # 跳过标题行
        header = next(reader, None)

        for row in reader:
            if len(row) < 2:
                skipped += 1
                continue

            source = row[0].strip()
            target = row[1].strip()
            category = row[2].strip() if len(row) > 2 else ''
            notes = row[3].strip() if len(row) > 3 else ''

            if source and target:
                self.add_term(glossary_name, source, target, notes, category)
                imported += 1
            else:
                skipped += 1

        return imported, skipped

    def get_all_terms(self, glossary_name: str = None) -> List[Dict]:
        """
        获取所有术语

        Args:
            glossary_name: 指定术语表（可选）

        Returns:
            术语列表
        """
        results = []

        glossaries = {glossary_name: self.active_glossaries[glossary_name]} \
            if glossary_name and glossary_name in self.active_glossaries \
            else self.active_glossaries

        for name, glossary in glossaries.items():
            for source, info in glossary.get('terms', {}).items():
                results.append({
                    'glossary': name,
                    'source': source,
                    **info
                })

        return results


# 全局实例
_default_gm = None

def get_glossary_manager() -> GlossaryManager:
    """获取默认的术语表管理器实例"""
    global _default_gm
    if _default_gm is None:
        _default_gm = GlossaryManager()
    return _default_gm


if __name__ == '__main__':
    # 测试代码
    print("术语表管理模块测试")
    print("=" * 50)

    gm = GlossaryManager()

    # 创建测试术语表
    gm.create_glossary('tech', '技术术语', 'English', '中文')
    gm.load_glossary('tech')

    # 添加术语
    gm.add_term('tech', 'API', '应用程序接口', '全称 Application Programming Interface')
    gm.add_term('tech', 'machine learning', '机器学习')
    gm.add_term('tech', 'deep learning', '深度学习')
    gm.add_term('tech', 'neural network', '神经网络')

    # 测试查找
    term = gm.get_term('API')
    print(f"查找 'API': {term}")

    # 测试文本中查找
    test_text = "This API uses machine learning and deep learning algorithms."
    found = gm.find_terms_in_text(test_text)
    print(f"\n在文本中找到的术语: {found}")

    # 生成提示词注入
    prompt = gm.generate_prompt_injection(test_text)
    print(f"\n生成的提示词注入:\n{prompt}")

    # 列出术语表
    glossaries = gm.list_glossaries()
    print(f"\n可用术语表: {glossaries}")

    print("\n测试完成!")
