#! python
# -*- coding: utf-8 -*-
"""
配置管理 (Config Manager) 模块
统一管理应用程序配置，支持加密、备份和迁移

功能：
- 配置文件读写
- 自动备份和恢复
- 版本迁移
- API Key 加密存储（可选）
- 默认值管理
"""

import json
import os
import shutil
import base64
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from copy import deepcopy

from app_paths import get_app_dir, get_backup_dir


# 配置版本
CONFIG_VERSION = "2.3.1"

# 默认配置
DEFAULT_CONFIG = {
    'version': CONFIG_VERSION,
    'target_language': '中文',
    'segment_size': 800,
    'preview_limit': 10000,
    'max_consecutive_failures': 3,
    'translation_delay': 0.5,
    'use_translation_memory': True,
    'use_glossary': True,
    'api_configs': {
        'gemini': {
            'api_key': '',
            'model': 'gemini-2.5-flash',
            'temperature': 0.2
        },
        'openai': {
            'api_key': '',
            'model': 'gpt-3.5-turbo',
            'base_url': '',
            'temperature': 0.2
        },
        'claude': {
            'api_key': '',
            'model': 'claude-3-haiku-20240307',
            'temperature': 0.2
        },
        'deepseek': {
            'api_key': '',
            'model': 'deepseek-chat',
            'base_url': 'https://api.deepseek.com/v1',
            'temperature': 0.2
        },
        'lm_studio': {
            'api_key': 'lm-studio',
            'model': 'qwen2.5-7b-instruct-1m',
            'base_url': 'http://127.0.0.1:1234/v1',
            'temperature': 0.2
        },
        'custom': {
            'api_key': '',
            'model': '',
            'base_url': '',
            'temperature': 0.2
        }
    },
    'online_search': {
        'zlibrary': {
            'email': '',
            'password': '',
            'domain': 'https://singlelogin.re',
            'cookie': ''
        },
        'annas_archive': {
            'domain': 'https://annas-archive.li'
        },
        'download_path': 'downloads',
        'enable_zlibrary': False
    },
    'custom_local_models': {},
    'translation_style': '通俗小说 (Novel)',
    'concurrency': 1,
    'context_enabled': True,
    'selected_translation_api': 'Gemini API',
    'selected_analysis_api': 'Gemini API',
    'selected_retry_api': '本地 LM Studio',
    'ui': {
        'window_width': 950,
        'window_height': 750,
        'theme': 'default'
    }
}


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = None, backup_dir: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认在用户配置目录下
            backup_dir: 备份目录，默认 config_backups/
        """
        if config_path is None:
            config_path = self._default_config_path()

        self.config_path = Path(config_path)
        self.legacy_config_path = Path(__file__).parent / 'translator_config.json'

        if backup_dir is None:
            backup_dir = get_backup_dir()

        self.backup_dir = Path(backup_dir)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 当前配置
        self._config: Dict = deepcopy(DEFAULT_CONFIG)

        # 加密密钥（简单混淆，非安全加密）
        self._key = "book_translator_2024"

        self._migrate_legacy_config()

        # 自动加载配置
        self.load()

    @staticmethod
    def _default_app_dir() -> Path:
        """返回用户级配置目录，避免把运行态配置提交到仓库。"""
        return get_app_dir()

    @classmethod
    def _default_config_path(cls) -> Path:
        return cls._default_app_dir() / 'translator_config.json'

    def _migrate_legacy_config(self):
        """首次升级时，把仓库目录下的旧配置复制到用户配置目录。"""
        if self.config_path.exists() or not self.legacy_config_path.exists():
            return

        try:
            shutil.copy2(self.legacy_config_path, self.config_path)
            print(f"ℹ️ 已迁移旧配置到用户目录: {self.config_path}")
        except Exception as e:
            print(f"⚠️ 迁移旧配置失败: {e}")

    def _apply_env_overrides(self, config: Dict) -> Dict:
        """允许通过环境变量覆盖 API Key，避免把敏感信息写入文件。"""
        env_map = {
            'gemini': 'GEMINI_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'claude': 'ANTHROPIC_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'custom': 'CUSTOM_API_KEY',
            'lm_studio': 'LM_STUDIO_API_KEY',
        }

        for provider, env_name in env_map.items():
            value = os.getenv(env_name)
            if value and provider in config.get('api_configs', {}):
                config['api_configs'][provider]['api_key'] = value

        return config

    def _encode_key(self, value: str) -> str:
        """简单编码 API Key（非安全加密，仅防止明文显示）"""
        if not value:
            return value
        try:
            encoded = base64.b64encode(value.encode()).decode()
            return f"enc:{encoded}"
        except:
            return value

    def _decode_key(self, value: str) -> str:
        """解码 API Key"""
        if not value or not value.startswith("enc:"):
            return value
        try:
            encoded = value[4:]
            return base64.b64decode(encoded.encode()).decode()
        except:
            return value

    def _transform_sensitive_fields(self, config: Dict, decoder: bool = False) -> Dict:
        """对敏感字段进行轻量编码/解码。

        注意：这不是强加密，只是避免把敏感信息以明文形式直接落盘。
        """
        config = deepcopy(config)
        transform = self._decode_key if decoder else self._encode_key

        for provider in config.get('api_configs', {}).values():
            if isinstance(provider, dict) and provider.get('api_key'):
                provider['api_key'] = transform(provider['api_key'])

        for model in config.get('custom_local_models', {}).values():
            if isinstance(model, dict) and model.get('api_key'):
                model['api_key'] = transform(model['api_key'])

        zlib = config.get('online_search', {}).get('zlibrary', {})
        for field in ('email', 'password', 'cookie'):
            if zlib.get(field):
                zlib[field] = transform(zlib[field])

        return config

    def _encode_sensitive_values(self, config: Dict) -> Dict:
        return self._transform_sensitive_fields(config, decoder=False)

    def _decode_sensitive_values(self, config: Dict) -> Dict:
        return self._transform_sensitive_fields(config, decoder=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键 (如 'api_configs.gemini.api_key')
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, save: bool = True):
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
            save: 是否立即保存
        """
        keys = key.split('.')
        config = self._config

        # 遍历到最后一个键的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

        if save:
            self.save()

    def get_api_config(self, provider: str) -> Dict:
        """
        获取 API 配置

        Args:
            provider: 提供商名称

        Returns:
            API 配置字典
        """
        config = self.get(f'api_configs.{provider}', {})

        # 解码 API Key
        if 'api_key' in config:
            config = dict(config)
            config['api_key'] = self._decode_key(config['api_key'])

        return config

    def set_api_config(self, provider: str, config: Dict, save: bool = True):
        """
        设置 API 配置

        Args:
            provider: 提供商名称
            config: 配置字典
            save: 是否立即保存
        """
        # 编码 API Key（可选）
        # config = dict(config)
        # if 'api_key' in config:
        #     config['api_key'] = self._encode_key(config['api_key'])

        self.set(f'api_configs.{provider}', config, save=save)

    def get_custom_local_model(self, name: str) -> Optional[Dict]:
        """获取自定义本地模型配置"""
        return self.get(f'custom_local_models.{name}')

    def set_custom_local_model(self, name: str, config: Dict, save: bool = True):
        """设置自定义本地模型配置"""
        self.set(f'custom_local_models.{name}', config, save=save)

    def remove_custom_local_model(self, name: str, save: bool = True):
        """删除自定义本地模型配置"""
        models = self.get('custom_local_models', {})
        if name in models:
            del models[name]
            self.set('custom_local_models', models, save=save)

    def load(self) -> bool:
        """
        从文件加载配置

        Returns:
            是否加载成功
        """
        try:
            if not self.config_path.exists():
                self._config = self._apply_env_overrides(deepcopy(DEFAULT_CONFIG))
                print("ℹ️ 配置文件不存在，使用默认配置")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = self._decode_sensitive_values(json.load(f))

            # 版本检查和迁移
            loaded_version = loaded.get('version', '1.0')
            if self._needs_migration(loaded_version):
                loaded = self._migrate_config(loaded, loaded_version)
                print(f"ℹ️ 配置已从 v{loaded_version} 迁移到 v{CONFIG_VERSION}")

            # 合并默认值
            self._config = self._apply_env_overrides(self._merge_with_defaults(loaded))

            print(f"✓ 配置已加载: {self.config_path}")
            return True

        except json.JSONDecodeError as e:
            print(f"✗ 配置文件格式错误: {e}")
            if self._restore_from_backup():
                return True
            return False

        except Exception as e:
            print(f"✗ 加载配置失败: {e}")
            return False

    def save(self, create_backup: bool = True) -> bool:
        """
        保存配置到文件

        Args:
            create_backup: 是否创建备份

        Returns:
            是否保存成功
        """
        try:
            # 更新版本号
            self._config['version'] = CONFIG_VERSION

            # 创建备份
            if create_backup and self.config_path.exists():
                self._create_backup()

            # 保存配置
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            disk_config = self._encode_sensitive_values(deepcopy(self._config))
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(disk_config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"✗ 保存配置失败: {e}")
            return False

    def _create_backup(self):
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'config_backup_{timestamp}.json'
            shutil.copy2(self.config_path, backup_file)

            # 只保留最近的备份
            self._cleanup_backups(keep=5)

        except Exception as e:
            print(f"⚠️ 创建备份失败: {e}")

    def _cleanup_backups(self, keep: int = 5):
        """清理旧备份，只保留最近的几个"""
        backups = sorted(
            self.backup_dir.glob('config_backup_*.json'),
            reverse=True
        )

        for old_backup in backups[keep:]:
            try:
                old_backup.unlink()
            except:
                pass

    def _restore_from_backup(self) -> bool:
        """从备份恢复配置"""
        backups = sorted(
            self.backup_dir.glob('config_backup_*.json'),
            reverse=True
        )

        for backup in backups:
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    loaded = self._decode_sensitive_values(json.load(f))

                self._config = self._merge_with_defaults(loaded)
                print(f"✓ 已从备份恢复: {backup.name}")

                # 保存恢复的配置
                self.save(create_backup=False)
                return True

            except:
                continue

        return False

    def _needs_migration(self, version: str) -> bool:
        """检查是否需要迁移"""
        try:
            current = tuple(map(int, CONFIG_VERSION.split('.')))
            loaded = tuple(map(int, version.split('.')))
            return loaded < current
        except:
            return True

    def _migrate_config(self, config: Dict, from_version: str) -> Dict:
        """迁移旧版本配置"""
        # v1.x -> v2.x
        if from_version.startswith('1.') or 'api_configs' not in config:
            # 旧格式可能直接存储 API 配置
            new_config = deepcopy(DEFAULT_CONFIG)

            # 迁移旧的 API 配置
            for key in ['gemini', 'openai', 'custom', 'lm_studio']:
                if key in config:
                    new_config['api_configs'][key].update(config[key])

            # 迁移目标语言
            if 'target_language' in config:
                new_config['target_language'] = config['target_language']

            config = new_config

        # v2.0 -> v2.1
        if from_version == '2.0':
            # 添加新的配置项
            if 'use_translation_memory' not in config:
                config['use_translation_memory'] = True
            if 'use_glossary' not in config:
                config['use_glossary'] = True
            if 'claude' not in config.get('api_configs', {}):
                config['api_configs']['claude'] = DEFAULT_CONFIG['api_configs']['claude']
            if 'deepseek' not in config.get('api_configs', {}):
                config['api_configs']['deepseek'] = DEFAULT_CONFIG['api_configs']['deepseek']

        config['version'] = CONFIG_VERSION
        return config

    def _merge_with_defaults(self, config: Dict) -> Dict:
        """将加载的配置与默认值合并"""
        result = deepcopy(DEFAULT_CONFIG)

        def merge(base: Dict, override: Dict):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge(base[key], value)
                else:
                    base[key] = value

        merge(result, config)
        return result

    def reset_to_defaults(self, save: bool = True):
        """重置为默认配置"""
        self._config = deepcopy(DEFAULT_CONFIG)
        if save:
            self.save()

    def export_config(self, output_path: str, include_keys: bool = False) -> bool:
        """
        导出配置（可选择是否包含 API Key）

        Args:
            output_path: 输出路径
            include_keys: 是否包含 API Key

        Returns:
            是否导出成功
        """
        try:
            export_config = deepcopy(self._config)

            if not include_keys:
                # 移除 API Key
                for provider in export_config.get('api_configs', {}).values():
                    if 'api_key' in provider:
                        provider['api_key'] = ''

                for model in export_config.get('custom_local_models', {}).values():
                    if 'api_key' in model:
                        model['api_key'] = ''

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"导出配置失败: {e}")
            return False

    def import_config(self, input_path: str, merge: bool = True) -> bool:
        """
        导入配置

        Args:
            input_path: 输入路径
            merge: 是否与现有配置合并（否则完全替换）

        Returns:
            是否导入成功
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            if merge:
                # 合并配置
                def merge_dict(base, override):
                    for key, value in override.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            merge_dict(base[key], value)
                        elif value:  # 只覆盖非空值
                            base[key] = value

                merge_dict(self._config, imported)
            else:
                self._config = self._merge_with_defaults(imported)

            self.save()
            return True

        except Exception as e:
            print(f"导入配置失败: {e}")
            return False

    def get_all(self) -> Dict:
        """获取完整配置（副本）"""
        return deepcopy(self._config)

    def list_backups(self) -> list:
        """列出所有备份"""
        backups = []
        for backup in sorted(self.backup_dir.glob('config_backup_*.json'), reverse=True):
            try:
                stat = backup.stat()
                backups.append({
                    'name': backup.name,
                    'path': str(backup),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except:
                continue
        return backups


# 全局实例
_default_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取默认配置管理器实例"""
    global _default_config_manager
    if _default_config_manager is None:
        _default_config_manager = ConfigManager()
    return _default_config_manager


if __name__ == '__main__':
    # 测试代码
    print("配置管理模块测试")
    print("=" * 50)

    cm = ConfigManager()

    # 测试获取配置
    print(f"\n目标语言: {cm.get('target_language')}")
    print(f"分段大小: {cm.get('segment_size')}")
    print(f"Gemini 模型: {cm.get('api_configs.gemini.model')}")

    # 测试设置配置
    cm.set('target_language', 'English', save=False)
    print(f"修改后目标语言: {cm.get('target_language')}")

    # 重置
    cm.set('target_language', '中文', save=False)

    # 列出备份
    backups = cm.list_backups()
    print(f"\n备份列表 ({len(backups)} 个):")
    for b in backups[:3]:
        print(f"  - {b['name']}")

    print("\n测试完成!")
