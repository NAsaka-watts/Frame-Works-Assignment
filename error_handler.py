"""
Comprehensive error handling system for COVID-19 Research Analyzer.

This module provides application-wide error handling, user-friendly error messages,
and graceful degradation for component failures.
"""

import logging
import traceback
import sys
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
import streamlit as st
from datetime import datetime
import pandas as pd


class ErrorHandler:
    """Central error handling class for the application."""
    
    def __init__(self, logger_name: str = "covid_analyzer"):
        """
        Initialize the error handler.
        
        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self.error_count = 0
        self.error_history = []
        
    def handle_error(self, 
                    error: Exception, 
                    context: str = "Unknown", 
                    user_message: Optional[str] = None,
                    show_details: bool = False,
                    recovery_suggestions: Optional[list] = None) -> Dict[str, Any]:
        """
        Handle an error with comprehensive logging and user feedback.
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            user_message: Custom user-friendly message
            show_details: Whether to show technical details to user
            recovery_suggestions: List of recovery suggestions for the user
            
        Returns:
            Dictionary containing error information and user guidance
        """
        self.error_count += 1
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.error_count:03d}"
        
        # Log the error with full details
        self.logger.error(
            f"Error ID: {error_id} | Context: {context} | "
            f"Error: {type(error).__name__}: {str(error)}"
        )
        self.logger.debug(f"Full traceback for {error_id}:\n{traceback.format_exc()}")
        
        # Create error record
        error_record = {
            'error_id': error_id,
            'timestamp': datetime.now(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        # Store in error history (keep last 50 errors)
        self.error_history.append(error_record)
        if len(self.error_history) > 50:
            self.error_history.pop(0)
        
        # Generate user-friendly message
        if user_message is None:
            user_message = self._generate_user_message(error, context)
        
        # Generate recovery suggestions if not provided
        if recovery_suggestions is None:
            recovery_suggestions = self._generate_recovery_suggestions(error, context)
        
        # Display error to user
        self._display_error_to_user(
            error_id=error_id,
            user_message=user_message,
            error=error if show_details else None,
            recovery_suggestions=recovery_suggestions
        )
        
        return {
            'error_id': error_id,
            'handled': True,
            'user_message': user_message,
            'recovery_suggestions': recovery_suggestions
        }
    
    def _generate_user_message(self, error: Exception, context: str) -> str:
        """Generate a user-friendly error message based on error type and context."""
        error_type = type(error).__name__
        
        # Data loading errors
        if 'data_loader' in context.lower() or 'loading' in context.lower():
            if 'FileNotFoundError' in error_type or 'file not found' in str(error).lower():
                return ("📁 **Data File Not Found**\n\n"
                       "The COVID-19 research data file could not be located. "
                       "Please ensure you have uploaded the correct metadata.csv file from the CORD-19 dataset.")
            
            elif 'MemoryError' in error_type or 'memory' in str(error).lower():
                return ("💾 **Insufficient Memory**\n\n"
                       "The data file is too large for available memory. "
                       "Try using the sample data option or consider using a machine with more RAM.")
            
            elif 'PermissionError' in error_type:
                return ("🔒 **File Access Denied**\n\n"
                       "Cannot access the data file due to permission restrictions. "
                       "Please check file permissions or try uploading the file again.")
            
            else:
                return ("📊 **Data Loading Issue**\n\n"
                       "There was a problem loading your data file. "
                       "Please verify the file format and try again.")
        
        # Data processing errors
        elif 'data_processor' in context.lower() or 'processing' in context.lower():
            if 'ValueError' in error_type:
                return ("⚙️ **Data Processing Error**\n\n"
                       "The data format is not compatible with our processing pipeline. "
                       "Please ensure you're using a valid CORD-19 metadata file.")
            
            elif 'KeyError' in error_type:
                return ("🔑 **Missing Data Columns**\n\n"
                       "Required data columns are missing from your file. "
                       "Please verify you're using the complete CORD-19 metadata.csv file.")
            
            else:
                return ("🔄 **Processing Failed**\n\n"
                       "Data processing encountered an issue. "
                       "The application will continue with available data.")
        
        # Analysis errors
        elif 'analyzer' in context.lower() or 'analysis' in context.lower():
            return ("📈 **Analysis Error**\n\n"
                   "The analysis could not be completed with the current data. "
                   "This might be due to insufficient or incompatible data.")
        
        # Visualization errors
        elif 'visualizer' in context.lower() or 'visualization' in context.lower():
            return ("📊 **Visualization Error**\n\n"
                   "Could not generate the requested chart. "
                   "The data will be displayed in table format instead.")
        
        # Network/API errors
        elif 'network' in context.lower() or 'api' in context.lower():
            return ("🌐 **Connection Issue**\n\n"
                   "Network connectivity problem detected. "
                   "Please check your internet connection and try again.")
        
        # Generic error message
        else:
            return ("⚠️ **Unexpected Error**\n\n"
                   f"An unexpected issue occurred in {context}. "
                   "The application will attempt to continue with reduced functionality.")
    
    def _generate_recovery_suggestions(self, error: Exception, context: str) -> list:
        """Generate recovery suggestions based on error type and context."""
        suggestions = []
        error_type = type(error).__name__
        
        # Data loading recovery suggestions
        if 'data_loader' in context.lower():
            if 'FileNotFoundError' in error_type:
                suggestions.extend([
                    "Download the CORD-19 dataset from https://www.semanticscholar.org/cord19/download",
                    "Ensure the metadata.csv file is properly uploaded",
                    "Try using the sample data option for demonstration"
                ])
            elif 'MemoryError' in error_type:
                suggestions.extend([
                    "Use the sample data option for testing",
                    "Close other applications to free up memory",
                    "Consider using a machine with more RAM"
                ])
            else:
                suggestions.extend([
                    "Verify the file is a valid CSV format",
                    "Check that the file is not corrupted",
                    "Try re-downloading the CORD-19 dataset"
                ])
        
        # Data processing recovery suggestions
        elif 'data_processor' in context.lower():
            suggestions.extend([
                "The application will continue with available data",
                "Some analysis features may be limited",
                "Consider using a different data file if issues persist"
            ])
        
        # Analysis recovery suggestions
        elif 'analyzer' in context.lower():
            suggestions.extend([
                "Try filtering the data to a smaller subset",
                "Check if required data columns are available",
                "Some analysis results may be incomplete"
            ])
        
        # Visualization recovery suggestions
        elif 'visualizer' in context.lower():
            suggestions.extend([
                "Data will be displayed in table format",
                "Try refreshing the page",
                "Check if your browser supports interactive charts"
            ])
        
        # Generic recovery suggestions
        if not suggestions:
            suggestions.extend([
                "Try refreshing the page",
                "Check your internet connection",
                "Contact support if the issue persists"
            ])
        
        return suggestions
    
    def _display_error_to_user(self, 
                              error_id: str,
                              user_message: str, 
                              error: Optional[Exception] = None,
                              recovery_suggestions: Optional[list] = None):
        """Display error information to the user in Streamlit."""
        # Main error message
        st.error(user_message)
        
        # Recovery suggestions
        if recovery_suggestions:
            with st.expander("💡 **Recovery Suggestions**", expanded=True):
                for i, suggestion in enumerate(recovery_suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        # Technical details (if requested)
        if error and st.session_state.get('show_error_details', False):
            with st.expander("🔧 **Technical Details**"):
                st.code(f"Error ID: {error_id}")
                st.code(f"Error Type: {type(error).__name__}")
                st.code(f"Error Message: {str(error)}")
        
        # Error reporting option
        with st.expander("📧 **Report This Error**"):
            st.write(f"**Error ID:** `{error_id}`")
            st.write("Please include this Error ID when reporting the issue.")
            
            if st.button("Copy Error ID to Clipboard"):
                st.write("Error ID copied! (Note: Actual clipboard functionality requires additional setup)")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_history:
            return {'total_errors': 0, 'recent_errors': 0}
        
        recent_errors = [
            err for err in self.error_history 
            if (datetime.now() - err['timestamp']).seconds < 3600  # Last hour
        ]
        
        error_types = {}
        for err in self.error_history:
            error_type = err['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_types': error_types,
            'last_error': self.error_history[-1]['timestamp'] if self.error_history else None
        }


# Global error handler instance
global_error_handler = ErrorHandler()


def safe_execute(context: str = "Unknown", 
                user_message: Optional[str] = None,
                recovery_suggestions: Optional[list] = None,
                show_details: bool = False,
                fallback_value: Any = None):
    """
    Decorator for safe execution of functions with comprehensive error handling.
    
    Args:
        context: Context description for error logging
        user_message: Custom user-friendly error message
        recovery_suggestions: List of recovery suggestions
        show_details: Whether to show technical details
        fallback_value: Value to return if function fails
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                global_error_handler.handle_error(
                    error=e,
                    context=f"{func.__name__} ({context})",
                    user_message=user_message,
                    show_details=show_details,
                    recovery_suggestions=recovery_suggestions
                )
                return fallback_value
        return wrapper
    return decorator


def handle_streamlit_errors():
    """Set up global Streamlit error handling."""
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        global_error_handler.handle_error(
            error=exc_value,
            context="Streamlit Application",
            user_message="An unexpected error occurred in the application.",
            show_details=True
        )
    
    sys.excepthook = exception_handler


def create_error_boundary(component_name: str):
    """
    Create an error boundary for a specific component.
    
    Args:
        component_name: Name of the component for error context
    """
    def error_boundary_decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Handle the error gracefully
                error_info = global_error_handler.handle_error(
                    error=e,
                    context=f"{component_name} Component",
                    user_message=f"The {component_name} component encountered an issue and will be disabled temporarily.",
                    recovery_suggestions=[
                        f"The {component_name} feature is temporarily unavailable",
                        "Other application features should continue to work normally",
                        "Try refreshing the page to restore functionality"
                    ]
                )
                
                # Return a safe fallback
                if 'DataFrame' in str(type(args[0])) if args else False:
                    return pd.DataFrame()  # Return empty DataFrame for data functions
                elif 'dict' in func.__annotations__.get('return', ''):
                    return {}  # Return empty dict for analysis functions
                else:
                    return None  # Return None for other functions
        
        return wrapper
    return error_boundary_decorator


def display_error_dashboard():
    """Display error monitoring dashboard for debugging."""
    if st.session_state.get('debug_mode', False):
        with st.expander("🐛 **Error Monitoring Dashboard**"):
            stats = global_error_handler.get_error_statistics()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Errors", stats['total_errors'])
            with col2:
                st.metric("Recent Errors", stats['recent_errors'])
            with col3:
                if stats['last_error']:
                    st.metric("Last Error", stats['last_error'].strftime('%H:%M:%S'))
                else:
                    st.metric("Last Error", "None")
            
            if stats['error_types']:
                st.write("**Error Types:**")
                for error_type, count in stats['error_types'].items():
                    st.write(f"- {error_type}: {count}")
            
            # Toggle for showing error details
            st.session_state.show_error_details = st.checkbox(
                "Show technical error details",
                value=st.session_state.get('show_error_details', False)
            )


# Graceful degradation utilities

class GracefulDegradation:
    """Utilities for graceful degradation when components fail."""
    
    @staticmethod
    def fallback_data_display(df: pd.DataFrame, error_context: str = ""):
        """Display data in a simple table when advanced features fail."""
        st.warning(f"Advanced features unavailable{': ' + error_context if error_context else ''}. Showing basic data view.")
        
        if not df.empty:
            # Show basic info
            st.write(f"**Dataset Info:** {len(df)} rows, {len(df.columns)} columns")
            
            # Show sample data
            st.write("**Sample Data:**")
            st.dataframe(df.head(10))
            
            # Show basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                st.write("**Basic Statistics:**")
                st.dataframe(df[numeric_cols].describe())
        else:
            st.error("No data available to display.")
    
    @staticmethod
    def fallback_chart_display(data: Union[Dict, pd.Series], chart_type: str = "table"):
        """Display data in table format when chart generation fails."""
        st.warning(f"Chart generation failed. Displaying data as {chart_type}.")
        
        if isinstance(data, dict):
            df = pd.DataFrame(list(data.items()), columns=['Category', 'Value'])
        elif isinstance(data, pd.Series):
            df = pd.DataFrame({'Category': data.index, 'Value': data.values})
        else:
            st.error("Cannot display data: unsupported format.")
            return
        
        st.dataframe(df)
    
    @staticmethod
    def fallback_analysis_display(message: str = "Analysis unavailable"):
        """Display fallback message when analysis fails."""
        st.info(f"📊 {message}")
        st.write("The analysis feature is temporarily unavailable. Please try:")
        st.write("- Refreshing the page")
        st.write("- Using a different data file")
        st.write("- Checking your data format")


# Initialize error handling system
def initialize_error_handling():
    """Initialize the comprehensive error handling system."""
    # Set up Streamlit error handling
    handle_streamlit_errors()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('covid_analyzer_errors.log')
        ]
    )
    
    global_error_handler.logger.info("Error handling system initialized")