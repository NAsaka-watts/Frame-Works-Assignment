"""
Performance optimization utilities for COVID-19 Research Analyzer.

This module provides data sampling, memory monitoring, and progress tracking for large datasets.
"""

import streamlit as st
import pandas as pd
import numpy as np
import psutil
import logging
from typing import Optional, Tuple, Dict, Any
import time
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage and provide warnings."""
    
    def __init__(self, warning_threshold: float = 0.8, critical_threshold: float = 0.9):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold (float): Memory usage percentage to trigger warning
            critical_threshold (float): Memory usage percentage to trigger critical alert
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.initial_memory = self.get_memory_usage()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dict[str, float]: Memory usage statistics
        """
        try:
            memory = psutil.virtual_memory()
            return {
                'total_gb': memory.total / (1024**3),
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3),
                'percentage': memory.percent,
                'free_gb': memory.free / (1024**3)
            }
        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            return {
                'total_gb': 0,
                'available_gb': 0,
                'used_gb': 0,
                'percentage': 0,
                'free_gb': 0
            }
    
    def check_memory_status(self) -> Tuple[str, str]:
        """
        Check current memory status and return status level and message.
        
        Returns:
            Tuple[str, str]: (status_level, message)
                status_level: 'ok', 'warning', 'critical'
        """
        memory_stats = self.get_memory_usage()
        usage_percent = memory_stats['percentage'] / 100
        
        if usage_percent >= self.critical_threshold:
            return 'critical', f"Critical memory usage: {memory_stats['percentage']:.1f}% ({memory_stats['available_gb']:.1f}GB available)"
        elif usage_percent >= self.warning_threshold:
            return 'warning', f"High memory usage: {memory_stats['percentage']:.1f}% ({memory_stats['available_gb']:.1f}GB available)"
        else:
            return 'ok', f"Memory usage: {memory_stats['percentage']:.1f}% ({memory_stats['available_gb']:.1f}GB available)"
    
    def display_memory_warning(self):
        """Display memory warning in Streamlit if needed."""
        status, message = self.check_memory_status()
        
        if status == 'critical':
            st.error(f"⚠️ {message}")
            st.error("Consider using data sampling or closing other applications to free memory.")
        elif status == 'warning':
            st.warning(f"⚠️ {message}")
            st.info("Consider using data sampling for better performance.")
        else:
            st.success(f"✅ {message}")


def create_data_sample(df: pd.DataFrame, sample_size: Optional[int] = None, 
                      sample_strategy: str = 'random') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Create a representative sample of the dataset for performance optimization.
    
    Args:
        df (pd.DataFrame): Original DataFrame
        sample_size (Optional[int]): Number of rows to sample. If None, auto-calculate
        sample_strategy (str): Sampling strategy ('random', 'stratified', 'systematic')
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: (sampled_df, sampling_info)
    """
    if df is None or df.empty:
        return df, {'error': 'DataFrame is empty or None'}
    
    original_size = len(df)
    
    # Auto-calculate sample size if not provided
    if sample_size is None:
        # Use adaptive sampling based on dataset size
        if original_size <= 1000:
            sample_size = original_size  # Use full dataset for small data
        elif original_size <= 10000:
            sample_size = min(5000, original_size)  # 50% for medium datasets
        elif original_size <= 100000:
            sample_size = min(10000, original_size)  # 10% for large datasets
        else:
            sample_size = min(20000, original_size)  # Max 20k for very large datasets
    
    # Ensure sample size doesn't exceed original size
    sample_size = min(sample_size, original_size)
    
    sampling_info = {
        'original_size': original_size,
        'sample_size': sample_size,
        'sampling_ratio': sample_size / original_size,
        'strategy': sample_strategy,
        'memory_saved_mb': 0
    }
    
    try:
        if sample_size >= original_size:
            # No sampling needed
            sampling_info['strategy'] = 'none'
            return df, sampling_info
        
        # Calculate memory savings
        original_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        if sample_strategy == 'random':
            sampled_df = df.sample(n=sample_size, random_state=42)
        elif sample_strategy == 'systematic':
            # Systematic sampling - every nth row
            step = original_size // sample_size
            indices = range(0, original_size, step)[:sample_size]
            sampled_df = df.iloc[indices]
        elif sample_strategy == 'stratified':
            # Stratified sampling by publication year if available
            if 'publication_year' in df.columns:
                sampled_df = df.groupby('publication_year', group_keys=False).apply(
                    lambda x: x.sample(min(len(x), max(1, int(sample_size * len(x) / original_size))), 
                                     random_state=42)
                ).reset_index(drop=True)
                # Ensure we don't exceed sample_size
                if len(sampled_df) > sample_size:
                    sampled_df = sampled_df.sample(n=sample_size, random_state=42)
            else:
                # Fallback to random sampling
                sampled_df = df.sample(n=sample_size, random_state=42)
        else:
            # Default to random sampling
            sampled_df = df.sample(n=sample_size, random_state=42)
        
        # Calculate actual memory savings
        sampled_memory = sampled_df.memory_usage(deep=True).sum() / (1024 * 1024)
        sampling_info['memory_saved_mb'] = original_memory - sampled_memory
        sampling_info['actual_sample_size'] = len(sampled_df)
        
        logger.info(f"Created sample: {len(sampled_df)} rows from {original_size} "
                   f"({sampling_info['sampling_ratio']:.2%}) using {sample_strategy} strategy")
        logger.info(f"Memory saved: {sampling_info['memory_saved_mb']:.1f}MB")
        
        return sampled_df, sampling_info
        
    except Exception as e:
        logger.error(f"Error creating data sample: {e}")
        return df, {'error': str(e)}


@contextmanager
def progress_tracker(operation_name: str, total_steps: int = 100):
    """
    Context manager for tracking progress of long-running operations.
    
    Args:
        operation_name (str): Name of the operation
        total_steps (int): Total number of steps
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()
    
    try:
        status_text.text(f"Starting {operation_name}...")
        
        class ProgressTracker:
            def __init__(self, progress_bar, status_text, total_steps, start_time):
                self.progress_bar = progress_bar
                self.status_text = status_text
                self.total_steps = total_steps
                self.current_step = 0
                self.start_time = start_time
            
            def update(self, step: int = None, message: str = None):
                if step is not None:
                    self.current_step = step
                else:
                    self.current_step += 1
                
                progress = min(self.current_step / self.total_steps, 1.0)
                self.progress_bar.progress(progress)
                
                elapsed_time = time.time() - self.start_time
                if progress > 0:
                    estimated_total = elapsed_time / progress
                    remaining_time = estimated_total - elapsed_time
                    time_info = f" (ETA: {remaining_time:.1f}s)"
                else:
                    time_info = ""
                
                if message:
                    self.status_text.text(f"{message}{time_info}")
                else:
                    self.status_text.text(f"{operation_name}: {progress:.1%}{time_info}")
        
        tracker = ProgressTracker(progress_bar, status_text, total_steps, start_time)
        yield tracker
        
    finally:
        # Clean up progress indicators
        progress_bar.progress(1.0)
        elapsed_time = time.time() - start_time
        status_text.text(f"✅ {operation_name} completed in {elapsed_time:.1f}s")
        time.sleep(0.5)  # Brief pause to show completion
        progress_bar.empty()
        status_text.empty()


def optimize_dataframe_memory(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Optimize DataFrame memory usage by converting data types.
    
    Args:
        df (pd.DataFrame): DataFrame to optimize
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: (optimized_df, optimization_info)
    """
    if df is None or df.empty:
        return df, {'error': 'DataFrame is empty or None'}
    
    optimization_info = {
        'original_memory_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
        'optimizations_applied': [],
        'memory_saved_mb': 0
    }
    
    optimized_df = df.copy()
    
    try:
        # Optimize object columns (strings)
        object_columns = optimized_df.select_dtypes(include=['object']).columns
        for col in object_columns:
            if optimized_df[col].dtype == 'object':
                # Convert to category if beneficial
                unique_ratio = optimized_df[col].nunique() / len(optimized_df)
                if unique_ratio < 0.5:  # Less than 50% unique values
                    optimized_df[col] = optimized_df[col].astype('category')
                    optimization_info['optimizations_applied'].append(f"{col}: object -> category")
        
        # Optimize integer columns
        int_columns = optimized_df.select_dtypes(include=['int64']).columns
        for col in int_columns:
            col_min = optimized_df[col].min()
            col_max = optimized_df[col].max()
            
            if col_min >= 0:  # Unsigned integers
                if col_max < 255:
                    optimized_df[col] = optimized_df[col].astype('uint8')
                    optimization_info['optimizations_applied'].append(f"{col}: int64 -> uint8")
                elif col_max < 65535:
                    optimized_df[col] = optimized_df[col].astype('uint16')
                    optimization_info['optimizations_applied'].append(f"{col}: int64 -> uint16")
                elif col_max < 4294967295:
                    optimized_df[col] = optimized_df[col].astype('uint32')
                    optimization_info['optimizations_applied'].append(f"{col}: int64 -> uint32")
            else:  # Signed integers
                if col_min > -128 and col_max < 127:
                    optimized_df[col] = optimized_df[col].astype('int8')
                    optimization_info['optimizations_applied'].append(f"{col}: int64 -> int8")
                elif col_min > -32768 and col_max < 32767:
                    optimized_df[col] = optimized_df[col].astype('int16')
                    optimization_info['optimizations_applied'].append(f"{col}: int64 -> int16")
                elif col_min > -2147483648 and col_max < 2147483647:
                    optimized_df[col] = optimized_df[col].astype('int32')
                    optimization_info['optimizations_applied'].append(f"{col}: int64 -> int32")
        
        # Optimize float columns
        float_columns = optimized_df.select_dtypes(include=['float64']).columns
        for col in float_columns:
            optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
            if optimized_df[col].dtype != 'float64':
                optimization_info['optimizations_applied'].append(f"{col}: float64 -> {optimized_df[col].dtype}")
        
        # Calculate memory savings
        final_memory_mb = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
        optimization_info['final_memory_mb'] = final_memory_mb
        optimization_info['memory_saved_mb'] = optimization_info['original_memory_mb'] - final_memory_mb
        optimization_info['memory_reduction_percent'] = (optimization_info['memory_saved_mb'] / optimization_info['original_memory_mb']) * 100
        
        logger.info(f"Memory optimization complete: {optimization_info['memory_saved_mb']:.1f}MB saved "
                   f"({optimization_info['memory_reduction_percent']:.1f}% reduction)")
        
        return optimized_df, optimization_info
        
    except Exception as e:
        logger.error(f"Error optimizing DataFrame memory: {e}")
        return df, {'error': str(e)}


def display_performance_metrics(df: pd.DataFrame, sampling_info: Dict[str, Any] = None, 
                              optimization_info: Dict[str, Any] = None):
    """
    Display performance metrics and optimization information.
    
    Args:
        df (pd.DataFrame): Current DataFrame
        sampling_info (Dict[str, Any]): Information about data sampling
        optimization_info (Dict[str, Any]): Information about memory optimization
    """
    with st.expander("📊 Performance Metrics"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Dataset Size", f"{len(df):,} rows")
            current_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
            st.metric("Memory Usage", f"{current_memory:.1f} MB")
        
        with col2:
            if sampling_info and 'sampling_ratio' in sampling_info:
                st.metric("Sampling Ratio", f"{sampling_info['sampling_ratio']:.1%}")
                if 'memory_saved_mb' in sampling_info:
                    st.metric("Memory Saved (Sampling)", f"{sampling_info['memory_saved_mb']:.1f} MB")
        
        with col3:
            if optimization_info and 'memory_saved_mb' in optimization_info:
                st.metric("Memory Saved (Optimization)", f"{optimization_info['memory_saved_mb']:.1f} MB")
                st.metric("Optimization Reduction", f"{optimization_info.get('memory_reduction_percent', 0):.1f}%")
        
        # Memory monitor
        memory_monitor = MemoryMonitor()
        memory_monitor.display_memory_warning()
        
        # Show optimization details
        if optimization_info and optimization_info.get('optimizations_applied'):
            st.write("**Applied Optimizations:**")
            for opt in optimization_info['optimizations_applied']:
                st.write(f"- {opt}")


def should_use_sampling(df: pd.DataFrame, memory_threshold_mb: float = 500) -> Tuple[bool, str]:
    """
    Determine if data sampling should be used based on dataset size and memory usage.
    
    Args:
        df (pd.DataFrame): DataFrame to evaluate
        memory_threshold_mb (float): Memory threshold in MB to trigger sampling
        
    Returns:
        Tuple[bool, str]: (should_sample, reason)
    """
    if df is None or df.empty:
        return False, "DataFrame is empty"
    
    current_memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    row_count = len(df)
    
    # Check memory usage
    if current_memory_mb > memory_threshold_mb:
        return True, f"Dataset uses {current_memory_mb:.1f}MB (threshold: {memory_threshold_mb}MB)"
    
    # Check row count
    if row_count > 50000:
        return True, f"Dataset has {row_count:,} rows (threshold: 50,000)"
    
    # Check system memory
    memory_monitor = MemoryMonitor()
    status, _ = memory_monitor.check_memory_status()
    if status in ['warning', 'critical']:
        return True, "System memory usage is high"
    
    return False, "Dataset size is manageable"


def create_performance_dashboard():
    """Create a performance monitoring dashboard in the sidebar."""
    with st.sidebar:
        with st.expander("⚡ Performance Monitor"):
            # Memory monitoring
            memory_monitor = MemoryMonitor()
            memory_stats = memory_monitor.get_memory_usage()
            
            st.write("**System Memory:**")
            st.write(f"- Used: {memory_stats['used_gb']:.1f}GB ({memory_stats['percentage']:.1f}%)")
            st.write(f"- Available: {memory_stats['available_gb']:.1f}GB")
            st.write(f"- Total: {memory_stats['total_gb']:.1f}GB")
            
            # Performance settings
            st.write("**Performance Settings:**")
            use_sampling = st.checkbox("Enable data sampling for large datasets", value=True)
            use_optimization = st.checkbox("Enable memory optimization", value=True)
            
            if use_sampling:
                sample_size = st.number_input("Max sample size", min_value=1000, max_value=50000, value=10000)
                st.session_state.performance_settings = {
                    'use_sampling': use_sampling,
                    'sample_size': sample_size,
                    'use_optimization': use_optimization
                }
            else:
                st.session_state.performance_settings = {
                    'use_sampling': False,
                    'use_optimization': use_optimization
                }