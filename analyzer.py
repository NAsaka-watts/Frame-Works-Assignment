"""
Analysis component for COVID-19 Research Analyzer.

This module handles statistical analysis and insight generation from CORD-19 metadata.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Union
import logging
from collections import Counter
import re
from datetime import datetime
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Custom exception for analysis errors."""
    pass


@st.cache_data(ttl=1800, show_spinner="Analyzing temporal trends...")
def analyze_temporal_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze temporal trends in COVID-19 research publications by counting papers by year.
    
    Args:
        df (pd.DataFrame): DataFrame containing research metadata with publication dates
        
    Returns:
        Dict[str, Any]: Dictionary containing temporal analysis results with:
            - 'papers_by_year': Dict mapping years to paper counts
            - 'total_papers_with_dates': Total number of papers with valid dates
            - 'date_range': Tuple of (earliest_year, latest_year)
            - 'peak_year': Year with most publications
            - 'trend_summary': Summary statistics
            
    Raises:
        AnalysisError: If temporal analysis fails
    """
    if df is None or df.empty:
        raise AnalysisError("Cannot analyze temporal trends: DataFrame is empty or None")
    
    logger.info("Analyzing temporal trends in research publications")
    
    try:
        # Check if we have publication year data
        year_column = None
        if 'publication_year' in df.columns:
            year_column = 'publication_year'
        elif 'publish_time' in df.columns:
            # Extract year from publish_time if publication_year doesn't exist
            logger.info("Extracting years from publish_time column")
            df_temp = df.copy()
            df_temp['publish_time'] = pd.to_datetime(df_temp['publish_time'], errors='coerce')
            df_temp['temp_year'] = df_temp['publish_time'].dt.year
            year_column = 'temp_year'
            df = df_temp
        
        if year_column is None:
            raise AnalysisError("No date columns found for temporal analysis")
        
        # Filter out invalid years
        valid_years = df[year_column].dropna()
        
        if valid_years.empty:
            logger.warning("No valid publication years found")
            return {
                'papers_by_year': {},
                'total_papers_with_dates': 0,
                'date_range': None,
                'peak_year': None,
                'trend_summary': 'No valid publication dates found'
            }
        
        # Count papers by year
        papers_by_year = valid_years.value_counts().sort_index().to_dict()
        
        # Convert numpy int64 keys to regular int for JSON serialization
        papers_by_year = {int(year): int(count) for year, count in papers_by_year.items()}
        
        # Calculate statistics
        total_papers_with_dates = len(valid_years)
        earliest_year = int(valid_years.min())
        latest_year = int(valid_years.max())
        peak_year = int(valid_years.value_counts().index[0])
        peak_count = int(valid_years.value_counts().iloc[0])
        
        # Calculate trend summary
        years_list = sorted(papers_by_year.keys())
        if len(years_list) >= 2:
            recent_years = [year for year in years_list if year >= latest_year - 2]
            if len(recent_years) >= 2:
                recent_trend = papers_by_year[recent_years[-1]] - papers_by_year[recent_years[0]]
                trend_direction = "increasing" if recent_trend > 0 else "decreasing" if recent_trend < 0 else "stable"
            else:
                trend_direction = "insufficient data"
        else:
            trend_direction = "insufficient data"
        
        trend_summary = (
            f"Publications span {earliest_year}-{latest_year}. "
            f"Peak year: {peak_year} ({peak_count} papers). "
            f"Recent trend: {trend_direction}."
        )
        
        logger.info(f"Temporal analysis complete: {total_papers_with_dates} papers analyzed")
        logger.info(f"Date range: {earliest_year} - {latest_year}")
        logger.info(f"Peak publication year: {peak_year} with {peak_count} papers")
        
        return {
            'papers_by_year': papers_by_year,
            'total_papers_with_dates': total_papers_with_dates,
            'date_range': (earliest_year, latest_year),
            'peak_year': peak_year,
            'trend_summary': trend_summary
        }
        
    except Exception as e:
        raise AnalysisError(f"Error in temporal trend analysis: {e}")


@st.cache_data(ttl=1800, show_spinner="Analyzing top journals...")
def get_top_journals(df: pd.DataFrame, n: int = 10) -> pd.Series:
    """
    Identify and rank top journals by publication count.
    
    Args:
        df (pd.DataFrame): DataFrame containing research metadata
        n (int): Number of top journals to return (default: 10)
        
    Returns:
        pd.Series: Series with journal names as index and publication counts as values,
                  sorted by count in descending order
                  
    Raises:
        AnalysisError: If journal analysis fails
    """
    if df is None or df.empty:
        raise AnalysisError("Cannot analyze journals: DataFrame is empty or None")
    
    if n <= 0:
        raise AnalysisError("Number of journals (n) must be positive")
    
    logger.info(f"Analyzing top {n} journals by publication count")
    
    try:
        # Check for journal column
        if 'journal' not in df.columns:
            raise AnalysisError("No 'journal' column found in DataFrame")
        
        # Get journal counts, excluding missing values
        journal_counts = df['journal'].value_counts()
        
        # Remove empty/null journals and common placeholder values
        placeholder_values = ['', 'unknown journal', 'unknown', 'n/a', 'na', None]
        journal_counts = journal_counts[~journal_counts.index.isin(placeholder_values)]
        
        if journal_counts.empty:
            logger.warning("No valid journal names found")
            return pd.Series(dtype='int64')
        
        # Get top n journals
        top_journals = journal_counts.head(n)
        
        logger.info(f"Found {len(journal_counts)} unique journals")
        logger.info(f"Top journal: '{top_journals.index[0]}' with {top_journals.iloc[0]} papers")
        
        return top_journals
        
    except Exception as e:
        raise AnalysisError(f"Error in journal analysis: {e}")


@st.cache_data(ttl=1800, show_spinner="Calculating source distribution...")
def calculate_source_distribution(df: pd.DataFrame) -> pd.Series:
    """
    Calculate distribution of papers by source.
    
    Args:
        df (pd.DataFrame): DataFrame containing research metadata
        
    Returns:
        pd.Series: Series with source names as index and paper counts as values,
                  sorted by count in descending order
                  
    Raises:
        AnalysisError: If source analysis fails
    """
    if df is None or df.empty:
        raise AnalysisError("Cannot analyze sources: DataFrame is empty or None")
    
    logger.info("Calculating source distribution")
    
    try:
        # Check for source column (CORD-19 uses 'source_x')
        source_column = None
        if 'source_x' in df.columns:
            source_column = 'source_x'
        elif 'source' in df.columns:
            source_column = 'source'
        
        if source_column is None:
            raise AnalysisError("No source column found in DataFrame")
        
        # Get source counts, excluding missing values
        source_counts = df[source_column].value_counts()
        
        # Remove empty/null sources and common placeholder values
        placeholder_values = ['', 'unknown source', 'unknown', 'n/a', 'na', None]
        source_counts = source_counts[~source_counts.index.isin(placeholder_values)]
        
        if source_counts.empty:
            logger.warning("No valid source names found")
            return pd.Series(dtype='int64')
        
        logger.info(f"Found {len(source_counts)} unique sources")
        logger.info(f"Top source: '{source_counts.index[0]}' with {source_counts.iloc[0]} papers")
        
        return source_counts
        
    except Exception as e:
        raise AnalysisError(f"Error in source distribution analysis: {e}")


@st.cache_data(ttl=1800, show_spinner="Extracting keywords from titles...")
def extract_title_keywords(df: pd.DataFrame, n: int = 100) -> Dict[str, int]:
    """
    Extract and count frequent words in paper titles for keyword analysis.
    
    Args:
        df (pd.DataFrame): DataFrame containing research metadata with titles
        n (int): Number of top keywords to return (default: 100)
        
    Returns:
        Dict[str, int]: Dictionary mapping keywords to their frequency counts,
                       sorted by frequency in descending order
                       
    Raises:
        AnalysisError: If keyword extraction fails
    """
    if df is None or df.empty:
        raise AnalysisError("Cannot extract keywords: DataFrame is empty or None")
    
    if n <= 0:
        raise AnalysisError("Number of keywords (n) must be positive")
    
    logger.info(f"Extracting top {n} keywords from paper titles")
    
    try:
        # Check for title column
        if 'title' not in df.columns:
            raise AnalysisError("No 'title' column found in DataFrame")
        
        # Get valid titles
        valid_titles = df['title'].dropna()
        
        if valid_titles.empty:
            logger.warning("No valid titles found")
            return {}
        
        # Clean and process titles
        all_words = []
        for title in valid_titles:
            if isinstance(title, str) and title.strip():
                # Clean the title text
                cleaned_title = _clean_text_for_keywords(title)
                # Extract words
                words = _extract_words_from_text(cleaned_title)
                all_words.extend(words)
        
        if not all_words:
            logger.warning("No words extracted from titles")
            return {}
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        # Get top n keywords
        top_keywords = dict(word_counts.most_common(n))
        
        logger.info(f"Extracted {len(word_counts)} unique words from {len(valid_titles)} titles")
        if top_keywords:
            top_word = list(top_keywords.keys())[0]
            logger.info(f"Most frequent keyword: '{top_word}' ({top_keywords[top_word]} occurrences)")
        
        return top_keywords
        
    except Exception as e:
        raise AnalysisError(f"Error in keyword extraction: {e}")


def _clean_text_for_keywords(text: str) -> str:
    """
    Clean text for keyword extraction by removing noise and normalizing.
    
    Args:
        text (str): Input text to clean
        
    Returns:
        str: Cleaned text ready for keyword extraction
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    cleaned = text.lower().strip()
    
    # Remove common punctuation but keep hyphens and apostrophes
    cleaned = re.sub(r'[^\w\s\-\']', ' ', cleaned)
    
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()


def _extract_words_from_text(text: str) -> List[str]:
    """
    Extract meaningful words from cleaned text, filtering out stop words and short words.
    
    Args:
        text (str): Cleaned text to extract words from
        
    Returns:
        List[str]: List of meaningful words
    """
    if not text:
        return []
    
    # Split into words
    words = text.split()
    
    # Define common stop words for biomedical/research text
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it',
        'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with', 'or', 'but', 'not', 'this',
        'these', 'they', 'were', 'been', 'their', 'said', 'each', 'which', 'she', 'do', 'how', 'if',
        'we', 'you', 'all', 'any', 'can', 'had', 'her', 'him', 'his', 'one', 'our', 'out', 'day',
        'get', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men',
        'put', 'say', 'too', 'use', 'was', 'yes', 'yet', 'also', 'back', 'call', 'came', 'come',
        'each', 'even', 'find', 'give', 'good', 'hand', 'here', 'just', 'keep', 'kind', 'know',
        'last', 'left', 'life', 'live', 'look', 'made', 'make', 'most', 'move', 'much', 'must',
        'name', 'need', 'next', 'only', 'open', 'over', 'own', 'part', 'play', 'right', 'same',
        'seem', 'show', 'side', 'some', 'take', 'tell', 'than', 'them', 'turn', 'very', 'want',
        'well', 'went', 'what', 'when', 'where', 'work', 'year', 'your', 'after', 'again', 'could',
        'every', 'first', 'found', 'great', 'group', 'house', 'large', 'place', 'right', 'small',
        'still', 'such', 'think', 'three', 'through', 'time', 'under', 'until', 'water', 'where',
        'while', 'world', 'would', 'write', 'young'
    }
    
    # Filter words
    meaningful_words = []
    for word in words:
        # Remove leading/trailing punctuation
        word = word.strip('-\'')
        
        # Skip if empty, too short, or is a stop word
        if len(word) < 3 or word in stop_words:
            continue
        
        # Skip if it's all numbers
        if word.isdigit():
            continue
        
        # Skip if it contains mostly numbers
        if sum(c.isdigit() for c in word) > len(word) / 2:
            continue
        
        meaningful_words.append(word)
    
    return meaningful_words


@st.cache_data(ttl=1800, show_spinner="Generating analysis summary...")
def get_analysis_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive statistical summary of the analysis results.
    
    Args:
        df (pd.DataFrame): DataFrame containing research metadata
        
    Returns:
        Dict[str, Any]: Dictionary containing comprehensive analysis summary
                       
    Raises:
        AnalysisError: If summary generation fails
    """
    if df is None or df.empty:
        raise AnalysisError("Cannot generate summary: DataFrame is empty or None")
    
    logger.info("Generating comprehensive analysis summary")
    
    try:
        summary = {
            'dataset_overview': {},
            'temporal_analysis': {},
            'journal_analysis': {},
            'source_analysis': {},
            'content_analysis': {}
        }
        
        # Dataset overview
        summary['dataset_overview'] = {
            'total_papers': len(df),
            'total_columns': len(df.columns),
            'available_columns': list(df.columns)
        }
        
        # Add basic statistics for key columns
        key_columns = ['title', 'abstract', 'authors', 'journal', 'source_x', 'publish_time']
        for col in key_columns:
            if col in df.columns:
                non_null_count = df[col].notna().sum()
                summary['dataset_overview'][f'{col}_coverage'] = {
                    'count': int(non_null_count),
                    'percentage': round(non_null_count / len(df) * 100, 1)
                }
        
        # Temporal analysis summary
        try:
            temporal_results = analyze_temporal_trends(df)
            summary['temporal_analysis'] = {
                'papers_with_dates': temporal_results['total_papers_with_dates'],
                'date_range': temporal_results['date_range'],
                'peak_year': temporal_results['peak_year'],
                'years_covered': len(temporal_results['papers_by_year']) if temporal_results['papers_by_year'] else 0
            }
        except Exception as e:
            summary['temporal_analysis'] = {'error': str(e)}
        
        # Journal analysis summary
        try:
            top_journals = get_top_journals(df, n=5)
            summary['journal_analysis'] = {
                'total_unique_journals': len(df['journal'].value_counts()) if 'journal' in df.columns else 0,
                'top_journal': top_journals.index[0] if not top_journals.empty else None,
                'top_journal_count': int(top_journals.iloc[0]) if not top_journals.empty else 0,
                'papers_with_journal_info': int(df['journal'].notna().sum()) if 'journal' in df.columns else 0
            }
        except Exception as e:
            summary['journal_analysis'] = {'error': str(e)}
        
        # Source analysis summary
        try:
            source_dist = calculate_source_distribution(df)
            summary['source_analysis'] = {
                'total_unique_sources': len(source_dist),
                'top_source': source_dist.index[0] if not source_dist.empty else None,
                'top_source_count': int(source_dist.iloc[0]) if not source_dist.empty else 0
            }
        except Exception as e:
            summary['source_analysis'] = {'error': str(e)}
        
        # Content analysis summary
        try:
            if 'title' in df.columns:
                keywords = extract_title_keywords(df, n=10)
                summary['content_analysis'] = {
                    'total_unique_keywords': len(keywords),
                    'top_keyword': list(keywords.keys())[0] if keywords else None,
                    'top_keyword_count': list(keywords.values())[0] if keywords else 0,
                    'papers_with_titles': int(df['title'].notna().sum())
                }
            else:
                summary['content_analysis'] = {'error': 'No title column available'}
        except Exception as e:
            summary['content_analysis'] = {'error': str(e)}
        
        # Add derived statistics if available
        if 'abstract_word_count' in df.columns:
            summary['content_analysis']['avg_abstract_words'] = round(df['abstract_word_count'].mean(), 1)
        
        if 'title_word_count' in df.columns:
            summary['content_analysis']['avg_title_words'] = round(df['title_word_count'].mean(), 1)
        
        if 'author_count' in df.columns:
            summary['content_analysis']['avg_authors_per_paper'] = round(df['author_count'].mean(), 1)
        
        logger.info("Analysis summary generated successfully")
        return summary
        
    except Exception as e:
        raise AnalysisError(f"Error generating analysis summary: {e}")


def validate_analysis_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate data quality for analysis and provide recommendations.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        
    Returns:
        Dict[str, Any]: Dictionary containing validation results and recommendations
    """
    if df is None or df.empty:
        return {'status': 'error', 'message': 'DataFrame is empty or None'}
    
    logger.info("Validating data quality for analysis")
    
    validation_results = {
        'status': 'valid',
        'warnings': [],
        'recommendations': [],
        'data_quality_score': 100
    }
    
    # Check for required columns
    required_columns = ['title']
    missing_required = [col for col in required_columns if col not in df.columns]
    if missing_required:
        validation_results['status'] = 'error'
        validation_results['warnings'].append(f"Missing required columns: {missing_required}")
        validation_results['data_quality_score'] -= 50
    
    # Check for important columns
    important_columns = ['journal', 'publish_time', 'abstract', 'authors']
    missing_important = [col for col in important_columns if col not in df.columns]
    if missing_important:
        validation_results['warnings'].append(f"Missing important columns: {missing_important}")
        validation_results['data_quality_score'] -= len(missing_important) * 10
    
    # Check data completeness
    if 'title' in df.columns:
        title_completeness = df['title'].notna().sum() / len(df) * 100
        if title_completeness < 90:
            validation_results['warnings'].append(f"Title completeness is low: {title_completeness:.1f}%")
            validation_results['data_quality_score'] -= (90 - title_completeness) / 2
    
    if 'publish_time' in df.columns:
        date_completeness = df['publish_time'].notna().sum() / len(df) * 100
        if date_completeness < 70:
            validation_results['warnings'].append(f"Date completeness is low: {date_completeness:.1f}%")
            validation_results['recommendations'].append("Consider temporal analysis limitations due to missing dates")
    
    # Check for duplicates
    if 'cord_uid' in df.columns:
        duplicate_count = df['cord_uid'].duplicated().sum()
        if duplicate_count > 0:
            validation_results['warnings'].append(f"Found {duplicate_count} duplicate paper IDs")
            validation_results['recommendations'].append("Consider removing duplicates before analysis")
    
    # Provide recommendations based on findings
    if validation_results['data_quality_score'] >= 90:
        validation_results['recommendations'].append("Data quality is excellent for comprehensive analysis")
    elif validation_results['data_quality_score'] >= 70:
        validation_results['recommendations'].append("Data quality is good, some analyses may have limitations")
    else:
        validation_results['recommendations'].append("Data quality issues detected, consider data cleaning")
    
    logger.info(f"Data validation complete. Quality score: {validation_results['data_quality_score']}")
    
    return validation_results