"""
Configuration module for COVID-19 Research Analyzer.

This module handles application settings, environment variables, and deployment configuration.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration class."""
    
    # Application settings
    app_title: str = "COVID-19 Research Analyzer"
    app_icon: str = "🦠"
    page_layout: str = "wide"
    
    # Data settings
    max_file_size_mb: int = 500
    sample_data_size: int = 100
    default_top_journals: int = 10
    default_top_keywords: int = 100
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    memory_threshold_mb: int = 1000
    enable_sampling: bool = True
    default_sample_size: int = 10000
    
    # UI settings
    sidebar_state: str = "expanded"
    theme: str = "light"
    show_debug_info: bool = False
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_structured_logging: bool = True
    
    # Deployment settings
    environment: str = "development"
    debug_mode: bool = True
    port: int = 8501
    host: str = "localhost"
    
    # Health check settings
    health_check_enabled: bool = True
    health_check_endpoint: str = "/health"
    
    # Security settings
    max_upload_size_mb: int = 100
    allowed_file_types: list = None
    
    def __post_init__(self):
        """Initialize default values that need to be mutable."""
        if self.allowed_file_types is None:
            self.allowed_file_types = ['csv']


def load_config_from_env() -> AppConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        AppConfig: Configuration object with values from environment variables
    """
    config = AppConfig()
    
    # Application settings
    config.app_title = os.getenv('COVID_ANALYZER_TITLE', config.app_title)
    config.app_icon = os.getenv('COVID_ANALYZER_ICON', config.app_icon)
    config.page_layout = os.getenv('COVID_ANALYZER_LAYOUT', config.page_layout)
    
    # Data settings
    config.max_file_size_mb = int(os.getenv('COVID_ANALYZER_MAX_FILE_SIZE_MB', config.max_file_size_mb))
    config.sample_data_size = int(os.getenv('COVID_ANALYZER_SAMPLE_SIZE', config.sample_data_size))
    config.default_top_journals = int(os.getenv('COVID_ANALYZER_TOP_JOURNALS', config.default_top_journals))
    config.default_top_keywords = int(os.getenv('COVID_ANALYZER_TOP_KEYWORDS', config.default_top_keywords))
    
    # Performance settings
    config.enable_caching = os.getenv('COVID_ANALYZER_ENABLE_CACHING', 'true').lower() == 'true'
    config.cache_ttl_seconds = int(os.getenv('COVID_ANALYZER_CACHE_TTL', config.cache_ttl_seconds))
    config.memory_threshold_mb = int(os.getenv('COVID_ANALYZER_MEMORY_THRESHOLD_MB', config.memory_threshold_mb))
    config.enable_sampling = os.getenv('COVID_ANALYZER_ENABLE_SAMPLING', 'true').lower() == 'true'
    config.default_sample_size = int(os.getenv('COVID_ANALYZER_SAMPLE_SIZE_DEFAULT', config.default_sample_size))
    
    # UI settings
    config.sidebar_state = os.getenv('COVID_ANALYZER_SIDEBAR_STATE', config.sidebar_state)
    config.theme = os.getenv('COVID_ANALYZER_THEME', config.theme)
    config.show_debug_info = os.getenv('COVID_ANALYZER_SHOW_DEBUG', 'false').lower() == 'true'
    
    # Logging settings
    config.log_level = os.getenv('COVID_ANALYZER_LOG_LEVEL', config.log_level)
    config.log_format = os.getenv('COVID_ANALYZER_LOG_FORMAT', config.log_format)
    config.enable_structured_logging = os.getenv('COVID_ANALYZER_STRUCTURED_LOGGING', 'true').lower() == 'true'
    
    # Deployment settings
    config.environment = os.getenv('COVID_ANALYZER_ENVIRONMENT', config.environment)
    config.debug_mode = os.getenv('COVID_ANALYZER_DEBUG', 'true').lower() == 'true'
    config.port = int(os.getenv('COVID_ANALYZER_PORT', config.port))
    config.host = os.getenv('COVID_ANALYZER_HOST', config.host)
    
    # Health check settings
    config.health_check_enabled = os.getenv('COVID_ANALYZER_HEALTH_CHECK', 'true').lower() == 'true'
    config.health_check_endpoint = os.getenv('COVID_ANALYZER_HEALTH_ENDPOINT', config.health_check_endpoint)
    
    # Security settings
    config.max_upload_size_mb = int(os.getenv('COVID_ANALYZER_MAX_UPLOAD_MB', config.max_upload_size_mb))
    
    allowed_types = os.getenv('COVID_ANALYZER_ALLOWED_TYPES', 'csv')
    config.allowed_file_types = [t.strip() for t in allowed_types.split(',')]
    
    logger.info(f"Configuration loaded for environment: {config.environment}")
    return config


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Database configuration dictionary
    """
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'covid_analyzer'),
        'username': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'ssl_mode': os.getenv('DB_SSL_MODE', 'prefer'),
        'connection_timeout': int(os.getenv('DB_TIMEOUT', '30')),
    }


def get_redis_config() -> Dict[str, Any]:
    """
    Get Redis configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Redis configuration dictionary
    """
    return {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'password': os.getenv('REDIS_PASSWORD', ''),
        'db': int(os.getenv('REDIS_DB', '0')),
        'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true',
        'connection_timeout': int(os.getenv('REDIS_TIMEOUT', '5')),
    }


def get_cloud_storage_config() -> Dict[str, Any]:
    """
    Get cloud storage configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Cloud storage configuration dictionary
    """
    return {
        'provider': os.getenv('CLOUD_STORAGE_PROVIDER', 'local'),  # local, aws, gcp, azure
        'bucket_name': os.getenv('CLOUD_STORAGE_BUCKET', ''),
        'region': os.getenv('CLOUD_STORAGE_REGION', 'us-east-1'),
        'access_key': os.getenv('CLOUD_STORAGE_ACCESS_KEY', ''),
        'secret_key': os.getenv('CLOUD_STORAGE_SECRET_KEY', ''),
        'endpoint_url': os.getenv('CLOUD_STORAGE_ENDPOINT', ''),
    }


def validate_config(config: AppConfig) -> bool:
    """
    Validate configuration settings.
    
    Args:
        config (AppConfig): Configuration object to validate
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    try:
        # Validate numeric values
        if config.max_file_size_mb <= 0:
            logger.error("max_file_size_mb must be positive")
            return False
        
        if config.port < 1 or config.port > 65535:
            logger.error("port must be between 1 and 65535")
            return False
        
        if config.cache_ttl_seconds < 0:
            logger.error("cache_ttl_seconds must be non-negative")
            return False
        
        # Validate string values
        valid_layouts = ['wide', 'centered']
        if config.page_layout not in valid_layouts:
            logger.error(f"page_layout must be one of: {valid_layouts}")
            return False
        
        valid_sidebar_states = ['auto', 'expanded', 'collapsed']
        if config.sidebar_state not in valid_sidebar_states:
            logger.error(f"sidebar_state must be one of: {valid_sidebar_states}")
            return False
        
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.log_level not in valid_log_levels:
            logger.error(f"log_level must be one of: {valid_log_levels}")
            return False
        
        valid_environments = ['development', 'staging', 'production']
        if config.environment not in valid_environments:
            logger.error(f"environment must be one of: {valid_environments}")
            return False
        
        # Validate file types
        if not config.allowed_file_types:
            logger.error("allowed_file_types cannot be empty")
            return False
        
        logger.info("Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def create_deployment_config(environment: str = "production") -> Dict[str, Any]:
    """
    Create deployment-specific configuration.
    
    Args:
        environment (str): Target deployment environment
        
    Returns:
        Dict[str, Any]: Deployment configuration dictionary
    """
    base_config = {
        'app_name': 'covid-research-analyzer',
        'version': '1.0.0',
        'description': 'COVID-19 Research Analyzer - Interactive data analysis and visualization',
        'author': 'COVID Research Team',
        'license': 'MIT',
    }
    
    if environment == "development":
        return {
            **base_config,
            'debug': True,
            'hot_reload': True,
            'log_level': 'DEBUG',
            'enable_profiling': True,
            'cors_origins': ['http://localhost:3000', 'http://localhost:8501'],
        }
    
    elif environment == "staging":
        return {
            **base_config,
            'debug': False,
            'hot_reload': False,
            'log_level': 'INFO',
            'enable_profiling': False,
            'cors_origins': ['https://staging.covid-analyzer.com'],
            'ssl_required': True,
        }
    
    elif environment == "production":
        return {
            **base_config,
            'debug': False,
            'hot_reload': False,
            'log_level': 'WARNING',
            'enable_profiling': False,
            'cors_origins': ['https://covid-analyzer.com'],
            'ssl_required': True,
            'rate_limiting': True,
            'monitoring_enabled': True,
        }
    
    else:
        raise ValueError(f"Unknown environment: {environment}")


def get_streamlit_config() -> Dict[str, Any]:
    """
    Get Streamlit-specific configuration.
    
    Returns:
        Dict[str, Any]: Streamlit configuration dictionary
    """
    config = load_config_from_env()
    
    return {
        'server': {
            'port': config.port,
            'address': config.host,
            'headless': config.environment != 'development',
            'enableCORS': False,
            'enableXsrfProtection': config.environment == 'production',
        },
        'browser': {
            'gatherUsageStats': False,
            'serverAddress': config.host,
            'serverPort': config.port,
        },
        'client': {
            'caching': config.enable_caching,
            'displayEnabled': True,
            'showErrorDetails': config.debug_mode,
        },
        'runner': {
            'magicEnabled': True,
            'installTracer': config.debug_mode,
            'fixMatplotlib': True,
        },
        'logger': {
            'level': config.log_level,
            'messageFormat': config.log_format,
        },
        'global': {
            'developmentMode': config.debug_mode,
            'logLevel': config.log_level,
            'unitTest': False,
        }
    }


# Global configuration instance
app_config = load_config_from_env()

# Validate configuration on import
if not validate_config(app_config):
    logger.warning("Configuration validation failed, using defaults")
    app_config = AppConfig()