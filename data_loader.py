"""
Data loading component for COVID-19 Research Analyzer.

This module handles loading and validation of CORD-19 metadata CSV files.
"""

import pandas as pd
import os
import sys
from typing import Dict, Any, Optional
import logging
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoadingError(Exception):
    """Custom exception for data loading errors."""
    pass


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class InsufficientMemoryError(Exception):
    """Custom exception for memory-related errors."""
    pass


@st.cache_data(ttl=3600, show_spinner="Loading metadata...")
def load_metadata(file_path: str) -> pd.DataFrame:
    """
    Load CORD-19 metadata from CSV file into pandas DataFrame with comprehensive error handling.
    
    Args:
        file_path (str): Path to the metadata CSV file
        
    Returns:
        pd.DataFrame: Loaded metadata DataFrame
        
    Raises:
        DataLoadingError: For various data loading issues with user-friendly messages
        InsufficientMemoryError: If the file is too large to load into memory
        DataValidationError: If the loaded data fails basic validation
    """
    try:
        # Validate input parameters
        if not file_path or not isinstance(file_path, str):
            raise DataLoadingError("Invalid file path provided. Please specify a valid path to the metadata CSV file.")
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = (
                f"Metadata file not found: {file_path}\n"
                "Please ensure you have downloaded the CORD-19 dataset and placed the metadata.csv file "
                "in the correct location. You can download it from: "
                "https://www.semanticscholar.org/cord19/download"
            )
            raise DataLoadingError(error_msg)
        
        # Check if it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            raise DataLoadingError(f"Path exists but is not a file: {file_path}")
        
        # Check file permissions
        if not os.access(file_path, os.R_OK):
            raise DataLoadingError(f"Permission denied: Cannot read file {file_path}")
        
        # Check file size and available memory
        file_size = os.path.getsize(file_path)
        available_memory = _get_available_memory()
        
        if file_size == 0:
            raise DataLoadingError(f"File is empty: {file_path}")
        
        # Estimate memory requirements (CSV files typically need 2-5x their size in RAM)
        estimated_memory_needed = file_size * 3
        
        if available_memory and estimated_memory_needed > available_memory:
            raise InsufficientMemoryError(
                f"Insufficient memory to load file. "
                f"File size: {file_size / (1024*1024):.1f}MB, "
                f"Estimated memory needed: {estimated_memory_needed / (1024*1024):.1f}MB, "
                f"Available memory: {available_memory / (1024*1024):.1f}MB"
            )
        
        logger.info(f"Loading metadata from: {file_path}")
        logger.info(f"File size: {file_size / (1024*1024):.1f}MB")
        
        try:
            # Load the CSV file
            df = pd.read_csv(file_path, low_memory=False)
            
            # Basic validation
            if df.empty:
                raise DataValidationError("Loaded DataFrame is empty")
            
            # Validate data structure
            validate_data_structure(df)
            
            logger.info(f"Successfully loaded {len(df)} records from {file_path}")
            return df
            
        except pd.errors.EmptyDataError:
            raise DataLoadingError(f"CSV file appears to be empty or corrupted: {file_path}")
        except pd.errors.ParserError as e:
            raise DataLoadingError(f"Error parsing CSV file: {e}")
        except MemoryError:
            raise InsufficientMemoryError(
                f"Not enough memory to load the file. Try using a machine with more RAM or "
                f"consider processing the file in chunks."
            )
        except Exception as e:
            raise DataLoadingError(f"Unexpected error loading metadata: {e}")
    
    except DataLoadingError:
        raise
    except InsufficientMemoryError:
        raise
    except DataValidationError:
        raise
    except Exception as e:
        raise DataLoadingError(f"Unexpected error in load_metadata: {e}")


def _get_available_memory() -> Optional[int]:
    """
    Get available system memory in bytes.
    
    Returns:
        Optional[int]: Available memory in bytes, or None if cannot determine
    """
    try:
        import psutil
        return psutil.virtual_memory().available
    except ImportError:
        # psutil not available, return None
        return None
    except Exception:
        # Any other error, return None
        return None


def validate_data_structure(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains required columns for CORD-19 analysis.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        
    Returns:
        bool: True if validation passes, False otherwise
        
    Raises:
        ValueError: If critical validation errors are found
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty or None")
    
    # Define required columns for CORD-19 metadata
    required_columns = [
        'paper_id',  # Unique identifier
        'title',     # Paper title
    ]
    
    # Define optional but commonly expected columns
    expected_columns = [
        'authors',
        'abstract', 
        'publish_time',
        'journal',
        'source_x',  # Common in CORD-19 dataset
        'url'
    ]
    
    missing_required = [col for col in required_columns if col not in df.columns]
    missing_expected = [col for col in expected_columns if col not in df.columns]
    
    # Check for required columns
    if missing_required:
        error_msg = f"Missing required columns: {missing_required}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Warn about missing expected columns
    if missing_expected:
        logger.warning(f"Missing expected columns (analysis may be limited): {missing_expected}")
    
    # Check for duplicate paper IDs
    if df['paper_id'].duplicated().any():
        duplicate_count = df['paper_id'].duplicated().sum()
        logger.warning(f"Found {duplicate_count} duplicate paper IDs")
    
    # Check data types and basic structure
    logger.info(f"DataFrame validation passed. Shape: {df.shape}")
    logger.info(f"Available columns: {list(df.columns)}")
    
    return True


@st.cache_data(ttl=1800, show_spinner="Generating data summary...")
def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate basic summary information about the dataset.
    
    Args:
        df (pd.DataFrame): DataFrame to summarize
        
    Returns:
        Dict[str, Any]: Dictionary containing summary statistics
    """
    if df is None or df.empty:
        return {"error": "DataFrame is empty or None"}
    
    summary = {
        "total_records": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "data_types": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
    }
    
    # Add column-specific summaries for key fields
    if 'paper_id' in df.columns:
        summary["unique_papers"] = df['paper_id'].nunique()
        summary["duplicate_papers"] = df['paper_id'].duplicated().sum()
    
    if 'title' in df.columns:
        summary["papers_with_titles"] = df['title'].notna().sum()
        summary["avg_title_length"] = df['title'].str.len().mean() if df['title'].notna().any() else 0
    
    if 'abstract' in df.columns:
        summary["papers_with_abstracts"] = df['abstract'].notna().sum()
        summary["avg_abstract_length"] = df['abstract'].str.len().mean() if df['abstract'].notna().any() else 0
    
    if 'publish_time' in df.columns:
        summary["papers_with_dates"] = df['publish_time'].notna().sum()
        # Try to get date range if possible
        try:
            dates = pd.to_datetime(df['publish_time'], errors='coerce')
            valid_dates = dates.dropna()
            if not valid_dates.empty:
                summary["date_range"] = {
                    "earliest": valid_dates.min().strftime('%Y-%m-%d'),
                    "latest": valid_dates.max().strftime('%Y-%m-%d')
                }
        except Exception:
            summary["date_range"] = "Unable to parse dates"
    
    if 'journal' in df.columns:
        summary["unique_journals"] = df['journal'].nunique()
        summary["papers_with_journal"] = df['journal'].notna().sum()
    
    logger.info("Generated data summary")
    return summary