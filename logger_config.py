"""
Comprehensive logging and debugging system for COVID-19 Research Analyzer.

This module provides structured logging, debug mode capabilities, and error reporting mechanisms.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import traceback
import streamlit as st
from pathlib import Path
import pandas as pd


class StructuredLogger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, name: str = "covid_analyzer", log_level: str = "INFO"):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.operation_stack = []
        
    def _setup_handlers(self):
        """Set up logging handlers for file and console output."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler with detailed logging
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "covid_analyzer.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Error-specific handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "covid_analyzer_errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # JSON structured log handler for analysis
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / "covid_analyzer_structured.jsonl",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(json_handler)
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation with context."""
        operation_id = f"{operation}_{datetime.now().strftime('%H%M%S_%f')}"
        self.operation_stack.append({
            'operation_id': operation_id,
            'operation': operation,
            'start_time': datetime.now(),
            'context': kwargs
        })
        
        self.logger.info(
            f"OPERATION_START: {operation}",
            extra={
                'operation_id': operation_id,
                'operation': operation,
                'session_id': self.session_id,
                'context': kwargs,
                'event_type': 'operation_start'
            }
        )
        return operation_id
    
    def log_operation_end(self, operation_id: str, success: bool = True, **kwargs):
        """Log the end of an operation with results."""
        # Find the operation in the stack
        operation_info = None
        for i, op in enumerate(self.operation_stack):
            if op['operation_id'] == operation_id:
                operation_info = self.operation_stack.pop(i)
                break
        
        if operation_info:
            duration = (datetime.now() - operation_info['start_time']).total_seconds()
            
            log_level = logging.INFO if success else logging.ERROR
            self.logger.log(
                log_level,
                f"OPERATION_END: {operation_info['operation']} ({'SUCCESS' if success else 'FAILED'}) - {duration:.2f}s",
                extra={
                    'operation_id': operation_id,
                    'operation': operation_info['operation'],
                    'session_id': self.session_id,
                    'duration_seconds': duration,
                    'success': success,
                    'context': operation_info['context'],
                    'result': kwargs,
                    'event_type': 'operation_end'
                }
            )
    
    def log_data_info(self, df: pd.DataFrame, context: str = ""):
        """Log information about a DataFrame."""
        if df is None:
            self.logger.warning(f"DATA_INFO: DataFrame is None - {context}")
            return
        
        info = {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'dtypes': df.dtypes.astype(str).to_dict()
        }
        
        self.logger.info(
            f"DATA_INFO: {context} - {info['rows']} rows, {info['columns']} columns",
            extra={
                'session_id': self.session_id,
                'context': context,
                'data_info': info,
                'event_type': 'data_info'
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """Log performance metrics."""
        self.logger.info(
            f"PERFORMANCE: {metric_name} = {value} {unit}",
            extra={
                'session_id': self.session_id,
                'metric_name': metric_name,
                'metric_value': value,
                'metric_unit': unit,
                'context': kwargs,
                'event_type': 'performance_metric'
            }
        )
    
    def log_user_action(self, action: str, **kwargs):
        """Log user actions for analytics."""
        self.logger.info(
            f"USER_ACTION: {action}",
            extra={
                'session_id': self.session_id,
                'action': action,
                'context': kwargs,
                'event_type': 'user_action'
            }
        )
    
    def log_error_with_context(self, error: Exception, context: str = "", **kwargs):
        """Log errors with full context and traceback."""
        self.logger.error(
            f"ERROR: {type(error).__name__}: {str(error)} - {context}",
            extra={
                'session_id': self.session_id,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'traceback': traceback.format_exc(),
                'additional_context': kwargs,
                'event_type': 'error'
            }
        )


class JSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'event_type'):
            log_entry['event_type'] = record.event_type
        if hasattr(record, 'operation_id'):
            log_entry['operation_id'] = record.operation_id
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        if hasattr(record, 'data_info'):
            log_entry['data_info'] = record.data_info
        if hasattr(record, 'metric_name'):
            log_entry['performance'] = {
                'metric': record.metric_name,
                'value': record.metric_value,
                'unit': getattr(record, 'metric_unit', '')
            }
        
        return json.dumps(log_entry)


class DebugMode:
    """Debug mode utilities for enhanced debugging capabilities."""
    
    def __init__(self, logger: StructuredLogger):
        """Initialize debug mode with logger."""
        self.logger = logger
        self.debug_info = {}
        self.performance_metrics = []
        
    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return st.session_state.get('debug_mode', False)
    
    def enable_debug_mode(self):
        """Enable debug mode."""
        st.session_state.debug_mode = True
        self.logger.log_user_action("debug_mode_enabled")
        st.success("🐛 Debug mode enabled")
    
    def disable_debug_mode(self):
        """Disable debug mode."""
        st.session_state.debug_mode = False
        self.logger.log_user_action("debug_mode_disabled")
        st.info("Debug mode disabled")
    
    def add_debug_info(self, key: str, value: Any):
        """Add information to debug context."""
        self.debug_info[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'type': type(value).__name__
        }
    
    def display_debug_panel(self):
        """Display comprehensive debug information panel."""
        if not self.is_debug_enabled():
            return
        
        with st.expander("🐛 **Debug Information Panel**", expanded=False):
            # Debug mode controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Disable Debug Mode"):
                    self.disable_debug_mode()
            with col2:
                if st.button("Clear Debug Info"):
                    self.debug_info.clear()
                    self.performance_metrics.clear()
                    st.success("Debug info cleared")
            
            # Session information
            st.subheader("Session Information")
            session_info = {
                'Session ID': self.logger.session_id,
                'Debug Mode': self.is_debug_enabled(),
                'Streamlit Version': st.__version__,
                'Python Version': sys.version.split()[0],
                'Current Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            for key, value in session_info.items():
                st.write(f"**{key}:** {value}")
            
            # Debug information
            if self.debug_info:
                st.subheader("Debug Context")
                debug_df = pd.DataFrame([
                    {
                        'Key': key,
                        'Value': str(info['value'])[:100] + ('...' if len(str(info['value'])) > 100 else ''),
                        'Type': info['type'],
                        'Timestamp': info['timestamp']
                    }
                    for key, info in self.debug_info.items()
                ])
                st.dataframe(debug_df)
            
            # Performance metrics
            if self.performance_metrics:
                st.subheader("Performance Metrics")
                metrics_df = pd.DataFrame(self.performance_metrics)
                st.dataframe(metrics_df)
            
            # Memory usage
            st.subheader("Memory Usage")
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                st.write(f"**RSS Memory:** {memory_info.rss / 1024 / 1024:.1f} MB")
                st.write(f"**VMS Memory:** {memory_info.vms / 1024 / 1024:.1f} MB")
                st.write(f"**Memory Percent:** {process.memory_percent():.1f}%")
            except ImportError:
                st.write("Install psutil for detailed memory information")
            
            # Session state
            st.subheader("Session State")
            if st.checkbox("Show Session State"):
                filtered_state = {
                    k: v for k, v in st.session_state.items() 
                    if not k.startswith('_') and k != 'debug_info'
                }
                st.json(filtered_state)
            
            # Log file information
            st.subheader("Log Files")
            log_dir = Path("logs")
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log*"))
                for log_file in log_files:
                    size_mb = log_file.stat().st_size / 1024 / 1024
                    st.write(f"**{log_file.name}:** {size_mb:.1f} MB")
            else:
                st.write("No log files found")
    
    def log_function_call(self, func_name: str, args: tuple, kwargs: dict):
        """Log function calls for debugging."""
        if self.is_debug_enabled():
            self.logger.logger.debug(
                f"FUNCTION_CALL: {func_name}",
                extra={
                    'session_id': self.logger.session_id,
                    'function_name': func_name,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                    'event_type': 'function_call'
                }
            )
    
    def add_performance_metric(self, name: str, value: float, unit: str = ""):
        """Add performance metric to debug info."""
        metric = {
            'name': name,
            'value': value,
            'unit': unit,
            'timestamp': datetime.now().isoformat()
        }
        self.performance_metrics.append(metric)
        self.logger.log_performance_metric(name, value, unit)


class ErrorReporting:
    """Error reporting mechanisms for the application."""
    
    def __init__(self, logger: StructuredLogger):
        """Initialize error reporting with logger."""
        self.logger = logger
        self.error_reports = []
    
    def create_error_report(self, 
                          error: Exception, 
                          context: str,
                          user_description: str = "",
                          include_data_sample: bool = False,
                          data_sample: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Create a comprehensive error report.
        
        Args:
            error: The exception that occurred
            context: Context where error occurred
            user_description: User's description of what they were doing
            include_data_sample: Whether to include a data sample
            data_sample: Sample of data being processed when error occurred
            
        Returns:
            Dictionary containing the error report
        """
        report_id = f"REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = {
            'report_id': report_id,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.logger.session_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'user_description': user_description,
            'traceback': traceback.format_exc(),
            'system_info': {
                'python_version': sys.version,
                'streamlit_version': st.__version__,
                'platform': sys.platform
            }
        }
        
        # Add data sample if requested
        if include_data_sample and data_sample is not None:
            try:
                report['data_sample'] = {
                    'shape': data_sample.shape,
                    'columns': list(data_sample.columns),
                    'dtypes': data_sample.dtypes.astype(str).to_dict(),
                    'sample_rows': data_sample.head(3).to_dict('records')
                }
            except Exception as e:
                report['data_sample_error'] = str(e)
        
        # Add session state (filtered)
        try:
            filtered_state = {
                k: str(v)[:100] for k, v in st.session_state.items() 
                if not k.startswith('_') and not callable(v)
            }
            report['session_state'] = filtered_state
        except Exception:
            report['session_state'] = "Could not capture session state"
        
        self.error_reports.append(report)
        self.logger.log_error_with_context(error, context, report_id=report_id)
        
        return report
    
    def display_error_report_form(self, error: Exception, context: str):
        """Display a form for users to submit error reports."""
        with st.expander("📧 **Submit Error Report**"):
            st.write("Help us improve the application by reporting this error:")
            
            user_description = st.text_area(
                "What were you trying to do when this error occurred?",
                placeholder="Describe the steps you took before the error happened..."
            )
            
            include_data = st.checkbox(
                "Include data sample in report (helps with debugging)",
                help="This will include a small sample of your data structure (no sensitive content)"
            )
            
            if st.button("Generate Error Report"):
                data_sample = None
                if include_data and 'current_dataframe' in st.session_state:
                    data_sample = st.session_state.current_dataframe
                
                report = self.create_error_report(
                    error=error,
                    context=context,
                    user_description=user_description,
                    include_data_sample=include_data,
                    data_sample=data_sample
                )
                
                st.success(f"Error report generated: {report['report_id']}")
                
                # Display report summary
                with st.expander("Report Summary"):
                    st.json({
                        'Report ID': report['report_id'],
                        'Error Type': report['error_type'],
                        'Context': report['context'],
                        'Timestamp': report['timestamp']
                    })
                
                # Option to download report
                report_json = json.dumps(report, indent=2)
                st.download_button(
                    label="📥 Download Error Report",
                    data=report_json,
                    file_name=f"error_report_{report['report_id']}.json",
                    mime="application/json"
                )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about error reports."""
        if not self.error_reports:
            return {'total_reports': 0}
        
        error_types = {}
        contexts = {}
        
        for report in self.error_reports:
            error_type = report['error_type']
            context = report['context']
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            contexts[context] = contexts.get(context, 0) + 1
        
        return {
            'total_reports': len(self.error_reports),
            'error_types': error_types,
            'contexts': contexts,
            'latest_report': self.error_reports[-1]['timestamp'] if self.error_reports else None
        }


# Global instances
structured_logger = StructuredLogger()
debug_mode = DebugMode(structured_logger)
error_reporting = ErrorReporting(structured_logger)


def setup_logging_and_debugging():
    """Initialize the comprehensive logging and debugging system."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Log system startup
    structured_logger.log_operation_start("application_startup")
    structured_logger.logger.info("COVID-19 Research Analyzer started")
    
    return structured_logger, debug_mode, error_reporting


def debug_function_decorator(func):
    """Decorator to add debug logging to functions."""
    def wrapper(*args, **kwargs):
        if debug_mode.is_debug_enabled():
            debug_mode.log_function_call(func.__name__, args, kwargs)
        
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            if debug_mode.is_debug_enabled():
                debug_mode.add_performance_metric(
                    f"{func.__name__}_duration", 
                    duration, 
                    "seconds"
                )
            
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            structured_logger.log_error_with_context(
                e, 
                f"Function: {func.__name__}",
                duration=duration
            )
            raise
    
    return wrapper


def log_dataframe_operation(operation: str, df_before: pd.DataFrame, df_after: pd.DataFrame):
    """Log DataFrame operations for debugging."""
    if debug_mode.is_debug_enabled():
        debug_mode.add_debug_info(f"{operation}_before", {
            'shape': df_before.shape if df_before is not None else None,
            'columns': list(df_before.columns) if df_before is not None else None
        })
        debug_mode.add_debug_info(f"{operation}_after", {
            'shape': df_after.shape if df_after is not None else None,
            'columns': list(df_after.columns) if df_after is not None else None
        })
        
        structured_logger.log_data_info(df_before, f"{operation}_input")
        structured_logger.log_data_info(df_after, f"{operation}_output")