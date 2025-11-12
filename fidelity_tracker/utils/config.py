"""
Configuration management using YAML
Supports environment variable substitution and default values
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import re


class Config:
    """Configuration manager"""

    DEFAULT_CONFIG = {
        'credentials': {
            'fidelity': {
                'username': '${FIDELITY_USERNAME}',
                'password': '${FIDELITY_PASSWORD}',
                'mfa_secret': '${FIDELITY_MFA_SECRET}'
            }
        },
        'sync': {
            'schedule': '0 18 * * *',  # Daily 6 PM
            'enrichment_schedule': '0 19 * * 0',  # Weekly Sunday 7 PM
            'headless': True
        },
        'enrichment': {
            'enabled': True,
            'delay_seconds': 3.0,
            'max_retries': 3
        },
        'storage': {
            'output_dir': '.',
            'retention_days': 90,
            'auto_cleanup': True,
            'formats': ['json', 'csv', 'sqlite']
        },
        'database': {
            'path': 'fidelity_portfolio.db'
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/portfolio-tracker.log',
            'rotation': '10 MB',
            'retention': '30 days'
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_path: Path to YAML config file (optional)
        """
        self.config_path = Path(config_path) if config_path else Path('config/config.yaml')
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = yaml.safe_load(f)
                    config = self._substitute_env_vars(config)
                    logger.debug(f"Loaded config from {self.config_path}")
                    return config
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
                logger.info("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.debug("No config file found, using defaults")
            return self.DEFAULT_CONFIG.copy()

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in config

        Supports ${VAR_NAME} and ${VAR_NAME:default} syntax
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Match ${VAR} or ${VAR:default}
            pattern = r'\$\{([^:}]+)(?::([^}]*))?\}'
            matches = re.finditer(pattern, config)

            result = config
            for match in matches:
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ''
                env_value = os.getenv(var_name, default_value)
                result = result.replace(match.group(0), env_value)

            return result
        else:
            return config

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file

        Args:
            path: Optional path to save (uses self.config_path if not provided)
        """
        save_path = Path(path) if path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(save_path, 'w') as f:
                yaml.safe_dump(self._config, f, default_flow_style=False, sort_keys=False)
            logger.success(f"Saved configuration to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Dot-separated path (e.g., 'credentials.fidelity.username')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation

        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_credentials(self) -> Dict[str, str]:
        """Get Fidelity credentials"""
        return {
            'username': self.get('credentials.fidelity.username'),
            'password': self.get('credentials.fidelity.password'),
            'mfa_secret': self.get('credentials.fidelity.mfa_secret')
        }

    def validate(self) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid
        """
        # Check required credentials
        creds = self.get_credentials()
        if not all(creds.values()):
            logger.error("Missing required credentials")
            return False

        # Check numeric values
        if not isinstance(self.get('enrichment.delay_seconds'), (int, float)):
            logger.error("enrichment.delay_seconds must be numeric")
            return False

        if not isinstance(self.get('enrichment.max_retries'), int):
            logger.error("enrichment.max_retries must be an integer")
            return False

        logger.success("Configuration validated successfully")
        return True

    def create_example(self, path: str = 'config/config.yaml.example') -> None:
        """
        Create an example configuration file

        Args:
            path: Path for example file
        """
        example_path = Path(path)
        example_path.parent.mkdir(parents=True, exist_ok=True)

        with open(example_path, 'w') as f:
            yaml.safe_dump(self.DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)

        logger.success(f"Created example configuration at {example_path}")

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dict-style setting"""
        self.set(key, value)
