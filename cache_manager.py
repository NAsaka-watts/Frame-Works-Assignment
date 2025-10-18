"""
Cache management utilities for COVID-19 Research Analyzer.

This module provides cache invalidation strategies and cache management functions.
"""

import streamlit as st
import logging
from typing import Optional, List
import hashlib
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_all_caches():
    """Clear all Streamlit caches."""
    try:
        st.cache_data.clear()
        logger.info("All caches cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        return False


def get_data_hash(df: pd.DataFrame) -> str:
    """
    Generate a hash for DataFrame to detect data changes.
    
    Args:
        df (pd.DataFrame): DataFrame to hash
        
    Returns:
        str: Hash string representing the DataFrame
    """
    try:
        # Create a hash based on DataFrame shape and sample of data
        shape_str = f"{df.shape[0]}x{df.shape[1]}"
        columns_str = "_".join(sorted(df.columns.tolist()))
        
        # Sample some data for hash (first and last few rows)
        sample_data = ""
        if len(df) > 0:
            sample_data = str(df.head(3).to_string()) + str(df.tail(3).to_string())
        
        combined_str = f"{shape_str}_{columns_str}_{sample_data}"
        return hashlib.md5(combined_str.encode()).hexdigest()
    except Exception as e:
        logger.warning(f"Could not generate data hash: {e}")
        return "unknown"


def should_invalidate_cache(current_data_hash: str, stored_hash: Optional[str] = None) -> bool:
    """
    Determine if cache should be invalidated based on data changes.
    
    Args:
        current_data_hash (str): Hash of current data
        stored_hash (Optional[str]): Previously stored hash
        
    Returns:
        bool: True if cache should be invalidated
    """
    if stored_hash is None:
        return True
    
    return current_data_hash != stored_hash


def get_cache_stats() -> dict:
    """
    Get cache statistics and information.
    
    Returns:
        dict: Cache statistics
    """
    try:
        # Note: Streamlit doesn't provide direct cache stats API
        # This is a placeholder for future implementation
        return {
            "cache_enabled": True,
            "message": "Cache statistics not available in current Streamlit version"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": str(e)}


def create_cache_key(df: pd.DataFrame, operation: str, **kwargs) -> str:
    """
    Create a cache key for operations based on data and parameters.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        operation (str): Operation name
        **kwargs: Additional parameters
        
    Returns:
        str: Cache key
    """
    try:
        data_hash = get_data_hash(df)
        params_str = "_".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
        cache_key = f"{operation}_{data_hash}_{params_str}"
        return hashlib.md5(cache_key.encode()).hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Could not create cache key: {e}")
        return f"{operation}_default"


def manage_cache_size():
    """
    Manage cache size by clearing old entries if needed.
    This is a placeholder for future cache size management.
    """
    try:
        # Streamlit handles cache size automatically
        # This function is for future enhancements
        logger.info("Cache size management - handled automatically by Streamlit")
    except Exception as e:
        logger.error(f"Error in cache size management: {e}")


def setup_cache_monitoring():
    """
    Set up cache monitoring and logging.
    """
    try:
        # Add cache monitoring to session state
        if 'cache_stats' not in st.session_state:
            st.session_state.cache_stats = {
                'cache_hits': 0,
                'cache_misses': 0,
                'last_cleared': None
            }
        
        logger.info("Cache monitoring initialized")
    except Exception as e:
        logger.error(f"Error setting up cache monitoring: {e}")


def display_cache_info():
    """Display cache information in Streamlit sidebar."""
    try:
        with st.sidebar:
            with st.expander("🔧 Cache Information"):
                st.write("**Cache Status:** Enabled")
                st.write("**TTL:** 30 minutes for analysis, 1 hour for data loading")
                
                if st.button("Clear All Caches"):
                    if clear_all_caches():
                        st.success("Caches cleared successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to clear caches")
                
                cache_stats = get_cache_stats()
                if "error" not in cache_stats:
                    st.write("**Cache Statistics:**")
                    for key, value in cache_stats.items():
                        st.write(f"- {key}: {value}")
    except Exception as e:
        logger.error(f"Error displaying cache info: {e}")