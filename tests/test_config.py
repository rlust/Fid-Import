"""
Unit tests for fidelity_tracker.utils.config module
"""

import pytest
import os
from pathlib import Path
from fidelity_tracker.utils.config import Config


@pytest.mark.unit
class TestConfig:
    """Test Config class"""

    def test_init_with_file(self, temp_config_file):
        """Test Config initialization with config file"""
        config = Config(temp_config_file)
        assert config.config_path == Path(temp_config_file)
        assert config.config is not None

    def test_init_without_file(self, temp_dir, monkeypatch):
        """Test Config initialization without config file"""
        # Change to temp directory so it doesn't find real config
        monkeypatch.chdir(temp_dir)

        config = Config()
        assert config.config is not None
        # Should use default config

    def test_get_simple_value(self, temp_config_file):
        """Test getting a simple configuration value"""
        config = Config(temp_config_file)
        value = config.get('enrichment.enabled')
        assert value is True

    def test_get_nested_value(self, temp_config_file):
        """Test getting a nested configuration value"""
        config = Config(temp_config_file)
        value = config.get('credentials.fidelity.username')
        assert value == 'test_user'

    def test_get_with_default(self, temp_config_file):
        """Test getting value with default fallback"""
        config = Config(temp_config_file)
        value = config.get('nonexistent.key', default='default_value')
        assert value == 'default_value'

    def test_get_nonexistent_no_default(self, temp_config_file):
        """Test getting nonexistent value without default"""
        config = Config(temp_config_file)
        value = config.get('nonexistent.key')
        assert value is None

    def test_set_simple_value(self, temp_config_file):
        """Test setting a simple configuration value"""
        config = Config(temp_config_file)
        config.set('enrichment.enabled', False)
        assert config.get('enrichment.enabled') is False

    def test_set_nested_value(self, temp_config_file):
        """Test setting a nested configuration value"""
        config = Config(temp_config_file)
        config.set('credentials.fidelity.username', 'new_user')
        assert config.get('credentials.fidelity.username') == 'new_user'

    def test_set_creates_nested_structure(self, temp_config_file):
        """Test that set() creates nested structure if it doesn't exist"""
        config = Config(temp_config_file)
        config.set('new.nested.value', 'test')
        assert config.get('new.nested.value') == 'test'

    def test_env_var_substitution(self, temp_config_file, mock_env_vars):
        """Test environment variable substitution"""
        config = Config(temp_config_file)

        # Config file has ${FIDELITY_USERNAME}
        username = config.get('credentials.fidelity.username')
        assert username == 'test_user'  # From environment

    def test_env_var_substitution_missing(self, temp_config_file, monkeypatch):
        """Test behavior when environment variable is missing"""
        # Remove all FIDELITY env vars
        for key in ['FIDELITY_USERNAME', 'FIDELITY_PASSWORD', 'FIDELITY_MFA_SECRET']:
            monkeypatch.delenv(key, raising=False)

        config = Config(temp_config_file)

        # Should keep the ${VAR} syntax if env var doesn't exist
        username = config.get('credentials.fidelity.username')
        assert '${' in str(username) or username == ''

    def test_get_credentials(self, temp_config_file, mock_env_vars):
        """Test getting credentials dictionary"""
        config = Config(temp_config_file)
        creds = config.get_credentials()

        assert 'username' in creds
        assert 'password' in creds
        assert 'mfa_secret' in creds
        assert creds['username'] == 'test_user'

    def test_get_credentials_with_headless(self, temp_config_file, mock_env_vars):
        """Test that get_credentials includes headless setting"""
        config = Config(temp_config_file)
        creds = config.get_credentials()

        assert 'headless' in creds
        assert creds['headless'] is True

    def test_save(self, temp_dir, mock_env_vars):
        """Test saving configuration to file"""
        config_path = temp_dir / "new_config.yaml"
        config = Config()

        config.set('test.value', 'test_data')
        config.config_path = config_path
        config.save()

        assert config_path.exists()

        # Load and verify
        import yaml
        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert data['test']['value'] == 'test_data'

    def test_validate_valid_config(self, temp_config_file):
        """Test validation of valid configuration"""
        config = Config(temp_config_file)

        # Should not raise any errors
        config.validate()

    def test_validate_missing_required_field(self, temp_dir):
        """Test validation fails for missing required fields"""
        import yaml

        # Create config missing required field
        invalid_config = {
            'credentials': {
                # Missing fidelity section
            }
        }

        config_path = temp_dir / "invalid_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(invalid_config, f)

        config = Config(str(config_path))

        # Validation should detect missing required fields
        with pytest.raises(ValueError):
            config.validate()

    def test_load_default_config(self, temp_dir, monkeypatch):
        """Test loading default configuration"""
        monkeypatch.chdir(temp_dir)

        config = Config()

        # Should have default values
        assert config.get('enrichment.delay_seconds') is not None
        assert config.get('storage.retention_days') is not None

    def test_get_with_dot_notation(self, temp_config_file):
        """Test dot notation for getting values"""
        config = Config(temp_config_file)

        assert config.get('enrichment.delay_seconds') == 3.0
        assert config.get('storage.retention_days') == 90
        assert config.get('database.path') == 'fidelity_portfolio.db'

    def test_config_immutability_without_save(self, temp_config_file):
        """Test that config changes don't affect file until save() is called"""
        config = Config(temp_config_file)

        original_value = config.get('enrichment.delay_seconds')
        config.set('enrichment.delay_seconds', 10.0)

        # Load fresh config from same file
        config2 = Config(temp_config_file)

        # Original file should be unchanged
        assert config2.get('enrichment.delay_seconds') == original_value

    def test_multiple_env_var_substitutions(self, temp_config_file, mock_env_vars):
        """Test substitution of multiple environment variables"""
        config = Config(temp_config_file)

        username = config.get('credentials.fidelity.username')
        password = config.get('credentials.fidelity.password')
        mfa_secret = config.get('credentials.fidelity.mfa_secret')

        assert username == 'test_user'
        assert password == 'test_pass'
        assert mfa_secret == 'TESTMFASECRET123'

    def test_get_list_value(self, temp_config_file):
        """Test getting list values from config"""
        config = Config(temp_config_file)
        formats = config.get('storage.formats')

        assert isinstance(formats, list)
        assert 'json' in formats
        assert 'csv' in formats
        assert 'sqlite' in formats

    def test_set_list_value(self, temp_config_file):
        """Test setting list values in config"""
        config = Config(temp_config_file)
        config.set('storage.formats', ['json', 'csv'])

        formats = config.get('storage.formats')
        assert len(formats) == 2
        assert 'json' in formats

    def test_config_directory_creation(self, temp_dir):
        """Test that config directory is created if it doesn't exist"""
        config_path = temp_dir / "subdir" / "config.yaml"

        config = Config()
        config.config_path = config_path
        config.set('test.value', 'test')
        config.save()

        assert config_path.parent.exists()
        assert config_path.exists()
