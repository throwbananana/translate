#! python
# -*- coding: utf-8 -*-
"""
閰嶇疆绠＄悊 (Config Manager) 妯″潡
缁熶竴绠＄悊搴旂敤绋嬪簭閰嶇疆锛屾敮鎸佸姞瀵嗐€佸浠藉拰杩佺Щ

鍔熻兘锛?
- 閰嶇疆鏂囦欢璇诲啓
- 鑷姩澶囦唤鍜屾仮澶?
- 鐗堟湰杩佺Щ
- API Key 杞婚噺缂栫爜瀛樺偍锛堝彲閫夛級
- 榛樿鍊肩鐞?
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


# 閰嶇疆鐗堟湰
CONFIG_VERSION = "2.3.1"

# 榛樿閰嶇疆
DEFAULT_CONFIG = {
    'version': CONFIG_VERSION,
    'target_language': '涓枃',
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
            'model': 'claude-haiku-4-5-20251001',
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
    'translation_style': '閫氫織灏忚 (Novel)',
    'concurrency': 1,
    'context_enabled': True,
    'selected_translation_api': 'Gemini API',
    'selected_analysis_api': 'Gemini API',
    'selected_retry_api': '鏈湴 LM Studio',
    'ui': {
        'window_width': 950,
        'window_height': 750,
        'theme': 'default'
    }
}


TRANSLATION_RUNTIME_KEYS = (
    'target_language',
    'segment_size',
    'preview_limit',
    'max_consecutive_failures',
    'translation_delay',
    'use_translation_memory',
    'use_glossary',
    'translation_style',
    'concurrency',
    'context_enabled',
)


class ConfigManager:
    """閰嶇疆绠＄悊鍣?""

    def __init__(self, config_path: str = None, backup_dir: str = None):
        """
        鍒濆鍖栭厤缃鐞嗗櫒

        Args:
            config_path: 閰嶇疆鏂囦欢璺緞锛岄粯璁ゅ湪鐢ㄦ埛閰嶇疆鐩綍涓?
            backup_dir: 澶囦唤鐩綍锛岄粯璁?config_backups/
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

        # 褰撳墠閰嶇疆
        self._config: Dict = deepcopy(DEFAULT_CONFIG)

        # 杞婚噺缂栫爜鏍囪锛堜粎閬垮厤鏄庢枃鏄剧ず锛屼笉鎻愪緵鐪熸瀹夊叏鎬э級
        self._key = "book_translator_2024"

        self._migrate_legacy_config()

        # 鑷姩鍔犺浇閰嶇疆
        self.load()

    @staticmethod
    def _default_app_dir() -> Path:
        """杩斿洖鐢ㄦ埛绾ч厤缃洰褰曪紝閬垮厤鎶婅繍琛屾€侀厤缃彁浜ゅ埌浠撳簱銆?""
        return get_app_dir()

    @classmethod
    def _default_config_path(cls) -> Path:
        return cls._default_app_dir() / 'translator_config.json'

    def _migrate_legacy_config(self):
        """棣栨鍗囩骇鏃讹紝鎶婁粨搴撶洰褰曚笅鐨勬棫閰嶇疆澶嶅埗鍒扮敤鎴烽厤缃洰褰曘€?""
        if self.config_path.exists() or not self.legacy_config_path.exists():
            return

        try:
            shutil.copy2(self.legacy_config_path, self.config_path)
            print(f"鈩癸笍 宸茶縼绉绘棫閰嶇疆鍒扮敤鎴风洰褰? {self.config_path}")
        except Exception as e:
            print(f"鈿狅笍 杩佺Щ鏃ч厤缃け璐? {e}")

    def _apply_env_overrides(self, config: Dict) -> Dict:
        """鍏佽閫氳繃鐜鍙橀噺瑕嗙洊 API Key锛屼紭鍏堜娇鐢ㄧ幆澧冨彉閲忎繚瀛樻晱鎰熶俊鎭€?""
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
        """绠€鍗曠紪鐮?API Key锛堥潪瀹夊叏鍔犲瘑锛屼粎闃叉鏄庢枃鏄剧ず锛?""
        if not value:
            return value
        try:
            encoded = base64.b64encode(value.encode()).decode()
            return f"enc:{encoded}"
        except:
            return value

    def _decode_key(self, value: str) -> str:
        """瑙ｇ爜 API Key"""
        if not value or not value.startswith("enc:"):
            return value
        try:
            encoded = value[4:]
            return base64.b64decode(encoded.encode()).decode()
        except:
            return value

    def _transform_sensitive_fields(self, config: Dict, decoder: bool = False) -> Dict:
        """瀵规晱鎰熷瓧娈佃繘琛岃交閲忕紪鐮?瑙ｇ爜銆?

        娉ㄦ剰锛氳繖涓嶆槸寮哄姞瀵嗭紝鍙槸閬垮厤鎶婃晱鎰熶俊鎭互鏄庢枃褰㈠紡鐩存帴钀界洏銆?
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
        鑾峰彇閰嶇疆鍊?

        Args:
            key: 閰嶇疆閿紝鏀寔鐐瑰彿鍒嗛殧鐨勫祵濂楅敭 (濡?'api_configs.gemini.api_key')
            default: 榛樿鍊?

        Returns:
            閰嶇疆鍊?
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
        璁剧疆閰嶇疆鍊?

        Args:
            key: 閰嶇疆閿紝鏀寔鐐瑰彿鍒嗛殧鐨勫祵濂楅敭
            value: 閰嶇疆鍊?
            save: 鏄惁绔嬪嵆淇濆瓨
        """
        keys = key.split('.')
        config = self._config

        # 閬嶅巻鍒版渶鍚庝竴涓敭鐨勭埗绾?
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 璁剧疆鍊?
        config[keys[-1]] = value

        if save:
            self.save()

    def get_translation_runtime_profile(self) -> Dict[str, Any]:
        """杩斿洖缈昏瘧杩愯鏃堕厤缃揩鐓с€?""
        profile: Dict[str, Any] = {}
        for key in TRANSLATION_RUNTIME_KEYS:
            profile[key] = deepcopy(self.get(key, DEFAULT_CONFIG.get(key)))
        return profile

    def update_translation_runtime_profile(self, profile: Dict[str, Any], save: bool = True):
        """鎵归噺鏇存柊缈昏瘧杩愯鏃堕厤缃€?""
        if not profile:
            return

        for key in TRANSLATION_RUNTIME_KEYS:
            if key in profile:
                self.set(key, deepcopy(profile[key]), save=False)

        if save:
            self.save()

    def get_api_config(self, provider: str) -> Dict:
        """
        鑾峰彇 API 閰嶇疆

        Args:
            provider: 鎻愪緵鍟嗗悕绉?

        Returns:
            API 閰嶇疆瀛楀吀
        """
        config = self.get(f'api_configs.{provider}', {})

        # 瑙ｇ爜 API Key
        if 'api_key' in config:
            config = dict(config)
            config['api_key'] = self._decode_key(config['api_key'])

        return config

    def set_api_config(self, provider: str, config: Dict, save: bool = True):
        """
        璁剧疆 API 閰嶇疆

        Args:
            provider: 鎻愪緵鍟嗗悕绉?
            config: 閰嶇疆瀛楀吀
            save: 鏄惁绔嬪嵆淇濆瓨
        """
        # 缂栫爜 API Key锛堝彲閫夛級
        # config = dict(config)
        # if 'api_key' in config:
        #     config['api_key'] = self._encode_key(config['api_key'])

        self.set(f'api_configs.{provider}', config, save=save)

    def get_custom_local_model(self, name: str) -> Optional[Dict]:
        """鑾峰彇鑷畾涔夋湰鍦版ā鍨嬮厤缃?""
        return self.get(f'custom_local_models.{name}')

    def set_custom_local_model(self, name: str, config: Dict, save: bool = True):
        """璁剧疆鑷畾涔夋湰鍦版ā鍨嬮厤缃?""
        self.set(f'custom_local_models.{name}', config, save=save)

    def remove_custom_local_model(self, name: str, save: bool = True):
        """鍒犻櫎鑷畾涔夋湰鍦版ā鍨嬮厤缃?""
        models = self.get('custom_local_models', {})
        if name in models:
            del models[name]
            self.set('custom_local_models', models, save=save)

    def load(self) -> bool:
        """
        浠庢枃浠跺姞杞介厤缃?

        Returns:
            鏄惁鍔犺浇鎴愬姛
        """
        try:
            if not self.config_path.exists():
                self._config = self._apply_env_overrides(deepcopy(DEFAULT_CONFIG))
                print("鈩癸笍 閰嶇疆鏂囦欢涓嶅瓨鍦紝浣跨敤榛樿閰嶇疆")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = self._decode_sensitive_values(json.load(f))

            # 鐗堟湰妫€鏌ュ拰杩佺Щ
            loaded_version = loaded.get('version', '1.0')
            if self._needs_migration(loaded_version):
                loaded = self._migrate_config(loaded, loaded_version)
                print(f"鈩癸笍 閰嶇疆宸蹭粠 v{loaded_version} 杩佺Щ鍒?v{CONFIG_VERSION}")

            # 鍚堝苟榛樿鍊?
            self._config = self._apply_env_overrides(self._merge_with_defaults(loaded))

            print(f"鉁?閰嶇疆宸插姞杞? {self.config_path}")
            return True

        except json.JSONDecodeError as e:
            print(f"鉁?閰嶇疆鏂囦欢鏍煎紡閿欒: {e}")
            if self._restore_from_backup():
                return True
            return False

        except Exception as e:
            print(f"鉁?鍔犺浇閰嶇疆澶辫触: {e}")
            return False

    def save(self, create_backup: bool = True) -> bool:
        """
        淇濆瓨閰嶇疆鍒版枃浠?

        Args:
            create_backup: 鏄惁鍒涘缓澶囦唤

        Returns:
            鏄惁淇濆瓨鎴愬姛
        """
        try:
            # 鏇存柊鐗堟湰鍙?
            self._config['version'] = CONFIG_VERSION

            # 鍒涘缓澶囦唤
            if create_backup and self.config_path.exists():
                self._create_backup()

            # 淇濆瓨閰嶇疆
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            disk_config = self._encode_sensitive_values(deepcopy(self._config))
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(disk_config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"鉁?淇濆瓨閰嶇疆澶辫触: {e}")
            return False

    def _create_backup(self):
        """鍒涘缓閰嶇疆澶囦唤"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'config_backup_{timestamp}.json'
            shutil.copy2(self.config_path, backup_file)

            # 鍙繚鐣欐渶杩戠殑澶囦唤
            self._cleanup_backups(keep=5)

        except Exception as e:
            print(f"鈿狅笍 鍒涘缓澶囦唤澶辫触: {e}")

    def _cleanup_backups(self, keep: int = 5):
        """娓呯悊鏃у浠斤紝鍙繚鐣欐渶杩戠殑鍑犱釜"""
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
        """浠庡浠芥仮澶嶉厤缃?""
        backups = sorted(
            self.backup_dir.glob('config_backup_*.json'),
            reverse=True
        )

        for backup in backups:
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    loaded = self._decode_sensitive_values(json.load(f))

                self._config = self._merge_with_defaults(loaded)
                print(f"鉁?宸蹭粠澶囦唤鎭㈠: {backup.name}")

                # 淇濆瓨鎭㈠鐨勯厤缃?
                self.save(create_backup=False)
                return True

            except:
                continue

        return False

    def _needs_migration(self, version: str) -> bool:
        """妫€鏌ユ槸鍚﹂渶瑕佽縼绉?""
        try:
            current = tuple(map(int, CONFIG_VERSION.split('.')))
            loaded = tuple(map(int, version.split('.')))
            return loaded < current
        except:
            return True

    def _migrate_config(self, config: Dict, from_version: str) -> Dict:
        """杩佺Щ鏃х増鏈厤缃?""
        # v1.x -> v2.x
        if from_version.startswith('1.') or 'api_configs' not in config:
            # 鏃ф牸寮忓彲鑳界洿鎺ュ瓨鍌?API 閰嶇疆
            new_config = deepcopy(DEFAULT_CONFIG)

            # 杩佺Щ鏃х殑 API 閰嶇疆
            for key in ['gemini', 'openai', 'custom', 'lm_studio']:
                if key in config:
                    new_config['api_configs'][key].update(config[key])

            # 杩佺Щ鐩爣璇█
            if 'target_language' in config:
                new_config['target_language'] = config['target_language']

            config = new_config

        # v2.0 -> v2.1
        if from_version == '2.0':
            # 娣诲姞鏂扮殑閰嶇疆椤?
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
        """灏嗗姞杞界殑閰嶇疆涓庨粯璁ゅ€煎悎骞?""
        result = deepcopy(DEFAULT_CONFIG)

        def merge(base: Dict, override: Dict):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge(base[key], value)
                else:
                    base[key] = value

        merge(result, config)

        claude_cfg = result.get('api_configs', {}).get('claude', {})
        if claude_cfg.get('model') == 'claude-haiku-4-5-20251001':
            claude_cfg['model'] = DEFAULT_CONFIG['api_configs']['claude']['model']

        return result

    def reset_to_defaults(self, save: bool = True):
        """閲嶇疆涓洪粯璁ら厤缃?""
        self._config = deepcopy(DEFAULT_CONFIG)
        if save:
            self.save()

    def export_config(self, output_path: str, include_keys: bool = False) -> bool:
        """
        瀵煎嚭閰嶇疆锛堝彲閫夋嫨鏄惁鍖呭惈 API Key锛?

        Args:
            output_path: 杈撳嚭璺緞
            include_keys: 鏄惁鍖呭惈 API Key

        Returns:
            鏄惁瀵煎嚭鎴愬姛
        """
        try:
            export_config = deepcopy(self._config)

            if not include_keys:
                # 绉婚櫎 API Key
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
            print(f"瀵煎嚭閰嶇疆澶辫触: {e}")
            return False

    def import_config(self, input_path: str, merge: bool = True) -> bool:
        """
        瀵煎叆閰嶇疆

        Args:
            input_path: 杈撳叆璺緞
            merge: 鏄惁涓庣幇鏈夐厤缃悎骞讹紙鍚﹀垯瀹屽叏鏇挎崲锛?

        Returns:
            鏄惁瀵煎叆鎴愬姛
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            if merge:
                # 鍚堝苟閰嶇疆
                def merge_dict(base, override):
                    for key, value in override.items():
                        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                            merge_dict(base[key], value)
                        elif value:  # 鍙鐩栭潪绌哄€?
                            base[key] = value

                merge_dict(self._config, imported)
            else:
                self._config = self._merge_with_defaults(imported)

            self.save()
            return True

        except Exception as e:
            print(f"瀵煎叆閰嶇疆澶辫触: {e}")
            return False

    def get_ui_runtime_profile(self) -> Dict:
        """杩斿洖 GUI 杩愯鏃朵細璇濇墍闇€鐨勬牳蹇冮厤缃揩鐓с€?""
        return {
            'api_configs': deepcopy(self.get('api_configs', {})),
            'custom_local_models': deepcopy(self.get('custom_local_models', {})),
            'target_language': self.get('target_language', DEFAULT_CONFIG['target_language']),
            'selected_translation_api': self.get('selected_translation_api', DEFAULT_CONFIG['selected_translation_api']),
            'selected_analysis_api': self.get('selected_analysis_api', DEFAULT_CONFIG['selected_analysis_api']),
            'selected_retry_api': self.get('selected_retry_api', DEFAULT_CONFIG['selected_retry_api']),
        }

    def update_ui_runtime_profile(
        self,
        *,
        api_configs: Optional[Dict] = None,
        custom_local_models: Optional[Dict] = None,
        target_language: Optional[str] = None,
        selected_translation_api: Optional[str] = None,
        selected_analysis_api: Optional[str] = None,
        selected_retry_api: Optional[str] = None,
        create_backup: bool = True,
    ) -> bool:
        """鎵归噺鏇存柊 GUI 杩愯鏃堕厤缃紝鍑忓皯鐣岄潰灞傞€愰」 set/save銆?""
        updates = {
            'api_configs': api_configs,
            'custom_local_models': custom_local_models,
            'target_language': target_language,
            'selected_translation_api': selected_translation_api,
            'selected_analysis_api': selected_analysis_api,
            'selected_retry_api': selected_retry_api,
        }

        for key, value in updates.items():
            if value is not None:
                self.set(key, deepcopy(value), save=False)

        return self.save(create_backup=create_backup)

    def get_all(self) -> Dict:
        """鑾峰彇瀹屾暣閰嶇疆锛堝壇鏈級"""
        return deepcopy(self._config)

    def list_backups(self) -> list:
        """鍒楀嚭鎵€鏈夊浠?""
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


# 鍏ㄥ眬瀹炰緥
_default_config_manager = None

def get_config_manager() -> ConfigManager:
    """鑾峰彇榛樿閰嶇疆绠＄悊鍣ㄥ疄渚?""
    global _default_config_manager
    if _default_config_manager is None:
        _default_config_manager = ConfigManager()
    return _default_config_manager


if __name__ == '__main__':
    # 娴嬭瘯浠ｇ爜
    print("閰嶇疆绠＄悊妯″潡娴嬭瘯")
    print("=" * 50)

    cm = ConfigManager()

    # 娴嬭瘯鑾峰彇閰嶇疆
    print(f"\n鐩爣璇█: {cm.get('target_language')}")
    print(f"鍒嗘澶у皬: {cm.get('segment_size')}")
    print(f"Gemini 妯″瀷: {cm.get('api_configs.gemini.model')}")

    # 娴嬭瘯璁剧疆閰嶇疆
    cm.set('target_language', 'English', save=False)
    print(f"淇敼鍚庣洰鏍囪瑷€: {cm.get('target_language')}")

    # 閲嶇疆
    cm.set('target_language', '涓枃', save=False)

    # 鍒楀嚭澶囦唤
    backups = cm.list_backups()
    print(f"\n澶囦唤鍒楄〃 ({len(backups)} 涓?:")
    for b in backups[:3]:
        print(f"  - {b['name']}")

    print("\n娴嬭瘯瀹屾垚!")

