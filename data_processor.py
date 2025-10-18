"""
Data processing component for COVID-19 Research Analyzer.

This module handles cleaning, preprocessing, and transformation of CORD-19 metadata.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import logging
import re
import warnings
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessingError(Exception):
    """Custom exception for data processing errors."""
    pass


@st.cache_data(ttl=1800, show_spinner="Cleaning missing values...")
def clean_missing_values(df: pd.DataFrame, strategy: str = 'smart') -> pd.DataFrame:
    """
    Clean missing values using various strategies.
    
    Args:
        df (pd.DataFrame): Input DataFrame to clean
        strategy (str): Strategy to use ('drop', 'fill', 'interpolate', 'smart')
            - 'drop': Remove rows with missing critical values
            - 'fill': Fill missing values with appropriate defaults
            - 'interpolate': Use interpolation for numerical columns
            - 'smart': Apply different strategies based on column type and importance
            
    Returns:
        pd.DataFrame: Cleaned DataFrame
        
    Raises:
        DataProcessingError: If cleaning fails or invalid strategy provided
    """
    if df is None or df.empty:
        raise DataProcessingError("Cannot clean missing values: DataFrame is empty or None")
    
    valid_strategies = ['drop', 'fill', 'interpolate', 'smart']
    if strategy not in valid_strategies:
        raise DataProcessingError(f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}")
    
    logger.info(f"Cleaning missing values using strategy: {strategy}")
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Log initial missing value counts
    initial_missing = cleaned_df.isnull().sum()
    logger.info(f"Initial missing values per column:\n{initial_missing[initial_missing > 0]}")
    
    try:
        if strategy == 'drop':
            cleaned_df = _clean_missing_drop(cleaned_df)
        elif strategy == 'fill':
            cleaned_df = _clean_missing_fill(cleaned_df)
        elif strategy == 'interpolate':
            cleaned_df = _clean_missing_interpolate(cleaned_df)
        elif strategy == 'smart':
            cleaned_df = _clean_missing_smart(cleaned_df)
        
        # Log final missing value counts
        final_missing = cleaned_df.isnull().sum()
        logger.info(f"Final missing values per column:\n{final_missing[final_missing > 0]}")
        logger.info(f"Rows before cleaning: {len(df)}, after cleaning: {len(cleaned_df)}")
        
        return cleaned_df
        
    except Exception as e:
        raise DataProcessingError(f"Error during missing value cleaning: {e}")


def _clean_missing_drop(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with missing values in critical columns."""
    critical_columns = ['cord_uid', 'title']  # Updated for CORD-19 dataset
    
    # Only drop if critical columns are missing
    available_critical = [col for col in critical_columns if col in df.columns]
    if available_critical:
        initial_rows = len(df)
        df_cleaned = df.dropna(subset=available_critical)
        dropped_rows = initial_rows - len(df_cleaned)
        logger.info(f"Dropped {dropped_rows} rows with missing critical values")
        return df_cleaned
    
    return df


def _clean_missing_fill(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing values with appropriate defaults."""
    df_filled = df.copy()
    
    # Define fill values for different column types
    fill_values = {
        'abstract': 'No abstract available',
        'authors': 'Unknown authors',
        'journal': 'Unknown journal',
        'doi': '',
        'pmcid': '',
        'pubmed_id': '',
        'license': 'unknown',
        'url': '',
        'source_x': 'Unknown source'
    }
    
    for column, fill_value in fill_values.items():
        if column in df_filled.columns:
            filled_count = df_filled[column].isnull().sum()
            if filled_count > 0:
                df_filled[column] = df_filled[column].fillna(fill_value)
                logger.info(f"Filled {filled_count} missing values in '{column}' with '{fill_value}'")
    
    return df_filled


def _clean_missing_interpolate(df: pd.DataFrame) -> pd.DataFrame:
    """Use interpolation for numerical columns."""
    df_interpolated = df.copy()
    
    # Identify numerical columns
    numerical_columns = df_interpolated.select_dtypes(include=[np.number]).columns
    
    for column in numerical_columns:
        if df_interpolated[column].isnull().any():
            initial_missing = df_interpolated[column].isnull().sum()
            df_interpolated[column] = df_interpolated[column].interpolate()
            final_missing = df_interpolated[column].isnull().sum()
            interpolated_count = initial_missing - final_missing
            if interpolated_count > 0:
                logger.info(f"Interpolated {interpolated_count} missing values in '{column}'")
    
    return df_interpolated


def _clean_missing_smart(df: pd.DataFrame) -> pd.DataFrame:
    """Apply smart cleaning strategy based on column importance and type."""
    df_smart = df.copy()
    
    # Critical columns - drop rows if missing
    critical_columns = ['cord_uid', 'title']  # Updated for CORD-19 dataset
    available_critical = [col for col in critical_columns if col in df_smart.columns]
    if available_critical:
        initial_rows = len(df_smart)
        df_smart = df_smart.dropna(subset=available_critical)
        dropped_rows = initial_rows - len(df_smart)
        if dropped_rows > 0:
            logger.info(f"Dropped {dropped_rows} rows with missing critical values")
    
    # Important columns - fill with meaningful defaults
    important_fill_values = {
        'abstract': 'No abstract available',
        'authors': 'Unknown authors',
        'journal': 'Unknown journal',
        'source_x': 'Unknown source'
    }
    
    for column, fill_value in important_fill_values.items():
        if column in df_smart.columns:
            filled_count = df_smart[column].isnull().sum()
            if filled_count > 0:
                df_smart[column] = df_smart[column].fillna(fill_value)
                logger.info(f"Filled {filled_count} missing values in '{column}'")
    
    # Optional columns - fill with empty strings
    optional_columns = ['doi', 'pmcid', 'pubmed_id', 'license', 'url', 'mag_id', 'who_covidence_id', 'arxiv_id', 'sha', 'pdf_json_files', 'pmc_json_files', 's2_id']
    for column in optional_columns:
        if column in df_smart.columns:
            filled_count = df_smart[column].isnull().sum()
            if filled_count > 0:
                df_smart[column] = df_smart[column].fillna('')
                logger.info(f"Filled {filled_count} missing values in '{column}' with empty string")
    
    return df_smart


@st.cache_data(ttl=1800, show_spinner="Processing dates...")
def process_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize date formats in the DataFrame.
    
    Args:
        df (pd.DataFrame): Input DataFrame with date columns
        
    Returns:
        pd.DataFrame: DataFrame with standardized date formats
        
    Raises:
        DataProcessingError: If date processing fails
    """
    if df is None or df.empty:
        raise DataProcessingError("Cannot process dates: DataFrame is empty or None")
    
    logger.info("Processing and standardizing date formats")
    
    processed_df = df.copy()
    
    # Common date column names in CORD-19 dataset
    date_columns = ['publish_time']
    
    try:
        for column in date_columns:
            if column in processed_df.columns:
                logger.info(f"Processing date column: {column}")
                
                # Count initial valid dates
                initial_valid = processed_df[column].notna().sum()
                
                # Convert to datetime with error handling
                # Try multiple date formats for better parsing
                processed_df[column] = pd.to_datetime(
                    processed_df[column], 
                    errors='coerce',
                    format='mixed'
                )
                
                # Count final valid dates
                final_valid = processed_df[column].notna().sum()
                failed_conversions = initial_valid - final_valid
                
                if failed_conversions > 0:
                    logger.warning(f"Failed to parse {failed_conversions} dates in column '{column}'")
                
                logger.info(f"Successfully processed {final_valid} dates in column '{column}'")
        
        return processed_df
        
    except Exception as e:
        raise DataProcessingError(f"Error processing dates: {e}")


@st.cache_data(ttl=1800, show_spinner="Extracting publication years...")
def extract_publication_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract publication year from date fields and create a new year column.
    
    Args:
        df (pd.DataFrame): Input DataFrame with date columns
        
    Returns:
        pd.DataFrame: DataFrame with added publication_year column
        
    Raises:
        DataProcessingError: If year extraction fails
    """
    if df is None or df.empty:
        raise DataProcessingError("Cannot extract publication year: DataFrame is empty or None")
    
    logger.info("Extracting publication year from date fields")
    
    year_df = df.copy()
    
    try:
        # First ensure dates are processed
        if 'publish_time' in year_df.columns:
            # Make sure publish_time is datetime
            if not pd.api.types.is_datetime64_any_dtype(year_df['publish_time']):
                year_df['publish_time'] = pd.to_datetime(year_df['publish_time'], errors='coerce')
            
            # Extract year
            year_df['publication_year'] = year_df['publish_time'].dt.year
            
            # Count successful extractions
            valid_years = year_df['publication_year'].notna().sum()
            logger.info(f"Successfully extracted {valid_years} publication years")
            
            # Log year range
            if valid_years > 0:
                min_year = year_df['publication_year'].min()
                max_year = year_df['publication_year'].max()
                logger.info(f"Publication year range: {min_year} - {max_year}")
        else:
            logger.warning("No 'publish_time' column found for year extraction")
        
        return year_df
        
    except Exception as e:
        raise DataProcessingError(f"Error extracting publication year: {e}")


@st.cache_data(ttl=1800, show_spinner="Creating derived columns...")
def create_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived columns for enhanced analysis.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with added derived columns
        
    Raises:
        DataProcessingError: If derived column creation fails
    """
    if df is None or df.empty:
        raise DataProcessingError("Cannot create derived columns: DataFrame is empty or None")
    
    logger.info("Creating derived columns for enhanced analysis")
    
    derived_df = df.copy()
    
    try:
        # Add abstract word count
        if 'abstract' in derived_df.columns:
            derived_df['abstract_word_count'] = derived_df['abstract'].apply(_count_words)
            logger.info("Added abstract_word_count column")
        
        # Add title word count
        if 'title' in derived_df.columns:
            derived_df['title_word_count'] = derived_df['title'].apply(_count_words)
            logger.info("Added title_word_count column")
        
        # Add abstract length (character count)
        if 'abstract' in derived_df.columns:
            derived_df['abstract_length'] = derived_df['abstract'].apply(_count_characters)
            logger.info("Added abstract_length column")
        
        # Add title length (character count)
        if 'title' in derived_df.columns:
            derived_df['title_length'] = derived_df['title'].apply(_count_characters)
            logger.info("Added title_length column")
        
        # Add has_abstract flag
        if 'abstract' in derived_df.columns:
            derived_df['has_abstract'] = derived_df['abstract'].apply(_has_meaningful_content)
            logger.info("Added has_abstract flag column")
        
        # Add has_doi flag
        if 'doi' in derived_df.columns:
            derived_df['has_doi'] = derived_df['doi'].apply(_has_meaningful_content)
            logger.info("Added has_doi flag column")
        
        # Add author count
        if 'authors' in derived_df.columns:
            derived_df['author_count'] = derived_df['authors'].apply(_count_authors)
            logger.info("Added author_count column")
        
        # Add processed title and abstract for text analysis
        if 'title' in derived_df.columns:
            derived_df['title_processed'] = derived_df['title'].apply(_preprocess_text)
            logger.info("Added title_processed column")
        
        if 'abstract' in derived_df.columns:
            derived_df['abstract_processed'] = derived_df['abstract'].apply(_preprocess_text)
            logger.info("Added abstract_processed column")
        
        return derived_df
        
    except Exception as e:
        raise DataProcessingError(f"Error creating derived columns: {e}")


def _count_words(text: Union[str, None]) -> int:
    """Count words in text, handling None and empty strings."""
    if pd.isna(text) or not isinstance(text, str) or text.strip() == '':
        return 0
    
    # Simple word count by splitting on whitespace
    words = text.strip().split()
    return len(words)


def _count_characters(text: Union[str, None]) -> int:
    """Count characters in text, handling None and empty strings."""
    if pd.isna(text) or not isinstance(text, str):
        return 0
    
    return len(text.strip())


def _has_meaningful_content(text: Union[str, None]) -> bool:
    """Check if text has meaningful content (not None, empty, or placeholder)."""
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    text = text.strip().lower()
    
    # Check for empty or placeholder content
    if text == '' or text in ['no abstract available', 'unknown', 'n/a', 'na']:
        return False
    
    return True


def _count_authors(authors_text: Union[str, None]) -> int:
    """Count number of authors from authors string."""
    if pd.isna(authors_text) or not isinstance(authors_text, str) or authors_text.strip() == '':
        return 0
    
    authors_text = authors_text.strip()
    
    # Handle common cases
    if authors_text.lower() in ['unknown authors', 'unknown', 'n/a', 'na']:
        return 0
    
    # Count authors by splitting on common separators
    # CORD-19 typically uses semicolons to separate authors
    if ';' in authors_text:
        authors = [author.strip() for author in authors_text.split(';') if author.strip()]
        return len(authors)
    
    # Fallback to comma separation
    if ',' in authors_text:
        authors = [author.strip() for author in authors_text.split(',') if author.strip()]
        return len(authors)
    
    # Single author
    return 1


def _preprocess_text(text: Union[str, None]) -> str:
    """
    Preprocess text for analysis by cleaning and normalizing.
    
    Args:
        text: Input text to preprocess
        
    Returns:
        str: Preprocessed text
    """
    if pd.isna(text) or not isinstance(text, str):
        return ''
    
    # Convert to lowercase
    processed = text.lower().strip()
    
    # Remove extra whitespace
    processed = re.sub(r'\s+', ' ', processed)
    
    # Remove special characters but keep letters, numbers, and basic punctuation
    processed = re.sub(r'[^\w\s\-\.]', ' ', processed)
    
    # Remove extra whitespace again
    processed = re.sub(r'\s+', ' ', processed).strip()
    
    return processed


def optimize_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame data types to reduce memory usage.
    
    Args:
        df (pd.DataFrame): Input DataFrame to optimize
        
    Returns:
        pd.DataFrame: DataFrame with optimized data types
        
    Raises:
        DataProcessingError: If optimization fails
    """
    if df is None or df.empty:
        raise DataProcessingError("Cannot optimize data types: DataFrame is empty or None")
    
    logger.info("Optimizing data types for memory efficiency")
    
    optimized_df = df.copy()
    
    try:
        # Log initial memory usage
        initial_memory = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
        logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Optimize string columns
        string_columns = optimized_df.select_dtypes(include=['object']).columns
        for column in string_columns:
            # Convert to category if the number of unique values is small relative to total
            unique_ratio = optimized_df[column].nunique() / len(optimized_df)
            if unique_ratio < 0.5:  # Less than 50% unique values
                optimized_df[column] = optimized_df[column].astype('category')
                logger.info(f"Converted '{column}' to category type")
        
        # Optimize integer columns
        int_columns = optimized_df.select_dtypes(include=['int64']).columns
        for column in int_columns:
            col_min = optimized_df[column].min()
            col_max = optimized_df[column].max()
            
            # Choose appropriate integer type based on range
            if col_min >= 0:  # Unsigned integers
                if col_max < 255:
                    optimized_df[column] = optimized_df[column].astype('uint8')
                elif col_max < 65535:
                    optimized_df[column] = optimized_df[column].astype('uint16')
                elif col_max < 4294967295:
                    optimized_df[column] = optimized_df[column].astype('uint32')
            else:  # Signed integers
                if col_min > -128 and col_max < 127:
                    optimized_df[column] = optimized_df[column].astype('int8')
                elif col_min > -32768 and col_max < 32767:
                    optimized_df[column] = optimized_df[column].astype('int16')
                elif col_min > -2147483648 and col_max < 2147483647:
                    optimized_df[column] = optimized_df[column].astype('int32')
            
            logger.info(f"Optimized integer column '{column}'")
        
        # Optimize float columns
        float_columns = optimized_df.select_dtypes(include=['float64']).columns
        for column in float_columns:
            # Try to convert to float32 if precision allows
            optimized_df[column] = pd.to_numeric(optimized_df[column], downcast='float')
            logger.info(f"Optimized float column '{column}'")
        
        # Log final memory usage
        final_memory = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
        memory_saved = initial_memory - final_memory
        logger.info(f"Final memory usage: {final_memory:.2f} MB")
        logger.info(f"Memory saved: {memory_saved:.2f} MB ({memory_saved/initial_memory*100:.1f}%)")
        
        return optimized_df
        
    except Exception as e:
        raise DataProcessingError(f"Error optimizing data types: {e}")


def get_text_preprocessing_utilities() -> Dict[str, Any]:
    """
    Get a dictionary of text preprocessing utility functions.
    
    Returns:
        Dict[str, Any]: Dictionary containing utility functions
    """
    return {
        'preprocess_text': _preprocess_text,
        'count_words': _count_words,
        'count_characters': _count_characters,
        'has_meaningful_content': _has_meaningful_content,
        'count_authors': _count_authors
    }