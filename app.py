"""
COVID-19 Research Analyzer - Streamlit Application

Main application interface for analyzing and visualizing CORD-19 research metadata.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional
import logging

# Import our custom modules
from data_loader import load_metadata, get_data_summary, DataLoadingError, InsufficientMemoryError, DataValidationError
from data_processor import clean_missing_values, process_dates, extract_publication_year, create_derived_columns, DataProcessingError
from analyzer import analyze_temporal_trends, get_top_journals, calculate_source_distribution, extract_title_keywords, get_analysis_summary, AnalysisError
from visualizer import create_temporal_plot, create_journal_bar_chart, create_distribution_chart, generate_word_cloud, create_responsive_layout, add_interactive_features
from performance_optimizer import (
    MemoryMonitor, create_data_sample, progress_tracker, optimize_dataframe_memory,
    display_performance_metrics, should_use_sampling, create_performance_dashboard
)
from cache_manager import display_cache_info, clear_all_caches

# Import comprehensive error handling
from error_handler import (
    global_error_handler, safe_execute, create_error_boundary, 
    display_error_dashboard, GracefulDegradation, initialize_error_handling
)

# Import logging and debugging system
from logger_config import (
    setup_logging_and_debugging, structured_logger, debug_mode, error_reporting,
    debug_function_decorator, log_dataframe_operation
)

# Import configuration and health check systems
from config import app_config, load_config_from_env
from health_check import health_checker, get_health_status, get_readiness_status

# Initialize error handling and logging systems
initialize_error_handling()
structured_logger, debug_mode, error_reporting = setup_logging_and_debugging()

# Configure logging
logging.basicConfig(level=getattr(logging, app_config.log_level))
logger = logging.getLogger(__name__)

# Page configuration using app config
st.set_page_config(
    page_title=app_config.app_title,
    page_icon=app_config.app_icon,
    layout=app_config.page_layout,
    initial_sidebar_state=app_config.sidebar_state
)

@safe_execute(
    context="Main Application",
    user_message="The application failed to start properly.",
    recovery_suggestions=[
        "Try refreshing the page",
        "Clear your browser cache",
        "Check your internet connection"
    ]
)
def main():
    """Main application function with comprehensive error handling."""
    
    try:
        # Log application start
        operation_id = structured_logger.log_operation_start("main_application_load")
        
        # Debug mode controls in sidebar
        with st.sidebar:
            st.markdown("---")
            st.subheader("🐛 Debug Controls")
            if not debug_mode.is_debug_enabled():
                if st.button("Enable Debug Mode"):
                    debug_mode.enable_debug_mode()
            else:
                if st.button("Disable Debug Mode"):
                    debug_mode.disable_debug_mode()
        
        # Display debug panel if enabled
        debug_mode.display_debug_panel()
        
        # Display error monitoring dashboard if in debug mode
        display_error_dashboard()
        
        # Main page structure with title and description
        st.title(f"{app_config.app_icon} {app_config.app_title}")
        st.markdown("""
        **Explore and analyze COVID-19 research publications from the CORD-19 dataset**
        
        This application provides interactive analysis and visualization of COVID-19 research metadata, 
        helping researchers understand publication trends, identify top journals, and explore research themes.
        """)
        
        # Add health status indicator if debug mode is enabled
        if app_config.show_debug_info:
            with st.expander("🔧 System Health Status"):
                health_status = get_health_status()
                status_color = {
                    'healthy': '🟢',
                    'degraded': '🟡', 
                    'unhealthy': '🔴'
                }.get(health_status['status'], '⚪')
                
                st.write(f"{status_color} **Status:** {health_status['status'].title()}")
                st.write(f"⏱️ **Uptime:** {health_status.get('uptime_seconds', 0):.0f} seconds")
                
                if health_status.get('failed_checks'):
                    st.warning(f"Failed checks: {', '.join(health_status['failed_checks'])}")
                
                if st.button("🔄 Refresh Health Status"):
                    st.rerun()
        
        # Log successful initialization
        structured_logger.log_operation_end(operation_id, success=True)
        
    except Exception as e:
        global_error_handler.handle_error(
            error=e,
            context="Main Application Initialization",
            user_message="Failed to initialize the application interface."
        )
        structured_logger.log_error_with_context(e, "Main Application Initialization")
        error_reporting.display_error_report_form(e, "Main Application Initialization")
        return
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.header("📊 Navigation & Controls")
        st.markdown("---")
        
        # Data loading section
        st.subheader("📁 Data Loading")
        data_file = st.file_uploader(
            "Upload CORD-19 metadata CSV file",
            type=['csv'],
            help="Upload the metadata.csv file from the CORD-19 dataset"
        )
        
        # Sample data option
        use_sample = st.checkbox(
            "Use sample data for demo",
            help="Use a small sample dataset for demonstration purposes"
        )
        
        st.markdown("---")
        
        # Performance monitoring dashboard
        create_performance_dashboard()
        
        # Cache management
        display_cache_info()
        
        st.markdown("---")
        
        # Logging and debugging controls
        st.subheader("🔧 System Controls")
        
        # Debug mode toggle
        debug_enabled = st.checkbox(
            "Enable Debug Mode",
            value=debug_mode.is_debug_enabled(),
            help="Show detailed debugging information and performance metrics"
        )
        
        if debug_enabled != debug_mode.is_debug_enabled():
            if debug_enabled:
                debug_mode.enable_debug_mode()
            else:
                debug_mode.disable_debug_mode()
        
        # Log level control
        if debug_mode.is_debug_enabled():
            log_level = st.selectbox(
                "Log Level",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=1,
                help="Set the logging verbosity level"
            )
            
            if st.button("Download Logs"):
                st.info("Log download functionality would be implemented here")
        
        st.markdown("---")
        
        # Analysis controls - will be populated when data is loaded
        st.subheader("⚙️ Analysis Settings")
        
        # Initialize session state for controls
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        
        if st.session_state.data_loaded:
            # Date range controls for temporal filtering
            st.subheader("📅 Date Range Filter")
            min_year = st.session_state.get('min_year', 2000)
            max_year = st.session_state.get('max_year', 2024)
            
            # Ensure min_year is less than max_year for slider
            if min_year >= max_year:
                max_year = min_year + 1
            
            date_range = st.slider(
                "Select publication year range",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
                help="Filter data by publication year range"
            )
            
            # Journal selection dropdown
            st.subheader("📚 Journal Filter")
            if 'available_journals' in st.session_state:
                selected_journals = st.multiselect(
                    "Select specific journals (optional)",
                    options=st.session_state.available_journals,
                    help="Leave empty to include all journals"
                )
            else:
                selected_journals = []
            
            # Source selection dropdown
            st.subheader("🔍 Source Filter")
            if 'available_sources' in st.session_state:
                selected_sources = st.multiselect(
                    "Select specific sources (optional)",
                    options=st.session_state.available_sources,
                    help="Leave empty to include all sources"
                )
            else:
                selected_sources = []
            
            # Top-N selection widgets
            st.subheader("🔢 Display Settings")
            top_journals_n = st.number_input(
                "Number of top journals to show",
                min_value=5,
                max_value=50,
                value=10,
                step=1,
                help="Select how many top journals to display in charts"
            )
            
            top_keywords_n = st.number_input(
                "Number of keywords for word cloud",
                min_value=20,
                max_value=200,
                value=100,
                step=10,
                help="Select how many keywords to include in word cloud"
            )
            
            # Store filter values in session state
            st.session_state.date_range = date_range
            st.session_state.selected_journals = selected_journals
            st.session_state.selected_sources = selected_sources
            st.session_state.top_journals_n = top_journals_n
            st.session_state.top_keywords_n = top_keywords_n
            
        else:
            st.info("Load data to access analysis controls")
    
    # Main content area with tabbed interface for different analysis sections
    if data_file is not None or use_sample:
        # Load and process data
        df = load_and_process_data(data_file, use_sample)
        
        if df is not None:
            # Apply filters based on user selections
            filtered_df = apply_filters(df)
            
            # Create tabs for different analysis sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📈 Temporal Trends", 
                "📚 Journal Analysis", 
                "🔍 Source Distribution", 
                "☁️ Content Analysis", 
                "📋 Data Overview"
            ])
            
            with tab1:
                st.header("Publication Trends Over Time")
                display_temporal_analysis(filtered_df)
            
            with tab2:
                st.header("Top Publishing Journals")
                display_journal_analysis(filtered_df)
            
            with tab3:
                st.header("Research Source Distribution")
                display_source_analysis(filtered_df)
            
            with tab4:
                st.header("Content and Keyword Analysis")
                display_content_analysis(filtered_df)
            
            with tab5:
                st.header("Dataset Overview and Statistics")
                display_data_overview(filtered_df)
    
    else:
        # Welcome message when no data is loaded
        st.info("""
        👋 **Welcome to the COVID-19 Research Analyzer!**
        
        To get started:
        1. Upload a CORD-19 metadata CSV file using the sidebar
        2. Or check "Use sample data for demo" to explore with sample data
        3. Navigate through the analysis tabs to explore different insights
        
        **About the CORD-19 Dataset:**
        The COVID-19 Open Research Dataset (CORD-19) is a resource of scholarly literature 
        about COVID-19, SARS-CoV-2, and related coronaviruses. You can download the dataset 
        from [Semantic Scholar](https://www.semanticscholar.org/cord19/download).
        """)
        
        # Add some helpful information
        with st.expander("📖 How to use this application"):
            st.markdown("""
            **Data Loading:**
            - Upload the `metadata.csv` file from the CORD-19 dataset
            - The application will automatically validate and process the data
            
            **Analysis Features:**
            - **Temporal Trends:** View publication counts over time
            - **Journal Analysis:** Identify top publishing journals
            - **Source Distribution:** Explore research sources
            - **Content Analysis:** Generate word clouds from paper titles
            - **Data Overview:** Browse raw data and statistics
            
            **Interactive Features:**
            - Filter data by date ranges and categories
            - Adjust visualization parameters
            - Export charts and data
            """)

@st.cache_data(show_spinner="Loading and processing data...")
@create_error_boundary("Data Loading")
@debug_function_decorator
def load_and_process_data(data_file, use_sample: bool) -> Optional[pd.DataFrame]:
    """Load and process the dataset with comprehensive error handling, logging, and caching for performance."""
    operation_id = structured_logger.log_operation_start("load_and_process_data", use_sample=use_sample)
    
    try:
        if use_sample:
            # Create sample data for demonstration
            st.info("Using sample data for demonstration")
            sample_data = {
                'cord_uid': [f'sample_{i}' for i in range(100)],
                'title': [f'Sample COVID-19 Research Paper {i}' for i in range(100)],
                'abstract': [f'This is a sample abstract about COVID-19 research topic {i}' for i in range(100)],
                'authors': [f'Author {i}; Co-Author {i}' for i in range(100)],
                'journal': [f'Journal {i % 10}' for i in range(100)],
                'source_x': [f'Source {i % 5}' for i in range(100)],
                'publish_time': pd.date_range('2020-01-01', periods=100, freq='D')
            }
            df = pd.DataFrame(sample_data)
        else:
            # Load real data from uploaded file
            with st.spinner("Loading and validating data..."):
                # Save uploaded file temporarily
                temp_path = "temp_metadata.csv"
                with open(temp_path, "wb") as f:
                    f.write(data_file.getbuffer())
                
                # Load using our data loader
                df = load_metadata(temp_path)
        
        # Log initial data info
        structured_logger.log_data_info(df, "raw_data_loaded")
        debug_mode.add_debug_info("raw_data_shape", df.shape)
        
        # Process the data with progress tracking
        with progress_tracker("Processing data", total_steps=5) as tracker:
            tracker.update(1, "Cleaning missing values...")
            df_before = df.copy()
            df = clean_missing_values(df, strategy='smart')
            log_dataframe_operation("clean_missing_values", df_before, df)
            
            tracker.update(2, "Processing dates...")
            df_before = df.copy()
            df = process_dates(df)
            log_dataframe_operation("process_dates", df_before, df)
            
            tracker.update(3, "Extracting publication years...")
            df_before = df.copy()
            df = extract_publication_year(df)
            log_dataframe_operation("extract_publication_year", df_before, df)
            
            tracker.update(4, "Creating derived columns...")
            df_before = df.copy()
            df = create_derived_columns(df)
            log_dataframe_operation("create_derived_columns", df_before, df)
            
            tracker.update(5, "Optimizing memory usage...")
            # Memory optimization
            df_before = df.copy()
            df, optimization_info = optimize_dataframe_memory(df)
            log_dataframe_operation("optimize_memory", df_before, df)
            
            # Store optimization info in session state
            st.session_state.optimization_info = optimization_info
        
        # Update session state with data info
        st.session_state.data_loaded = True
        
        # Set up filter options
        if 'publication_year' in df.columns:
            valid_years = df['publication_year'].dropna()
            if not valid_years.empty:
                st.session_state.min_year = int(valid_years.min())
                st.session_state.max_year = int(valid_years.max())
        
        if 'journal' in df.columns:
            journals = df['journal'].dropna().unique()
            st.session_state.available_journals = sorted([j for j in journals if j and j.strip()])
        
        if 'source_x' in df.columns:
            sources = df['source_x'].dropna().unique()
            st.session_state.available_sources = sorted([s for s in sources if s and s.strip()])
        elif 'source' in df.columns:
            sources = df['source'].dropna().unique()
            st.session_state.available_sources = sorted([s for s in sources if s and s.strip()])
        
        # Check if sampling should be used
        should_sample, reason = should_use_sampling(df)
        sampling_info = None
        
        if should_sample and st.session_state.get('performance_settings', {}).get('use_sampling', True):
            st.info(f"Large dataset detected ({reason}). Using data sampling for better performance.")
            sample_size = st.session_state.get('performance_settings', {}).get('sample_size', 10000)
            df, sampling_info = create_data_sample(df, sample_size=sample_size, sample_strategy='random')
            st.session_state.sampling_info = sampling_info
        
        # Display performance metrics
        display_performance_metrics(
            df, 
            sampling_info=sampling_info,
            optimization_info=st.session_state.get('optimization_info')
        )
        
        # Store current dataframe for error reporting
        st.session_state.current_dataframe = df
        
        # Log final data info
        structured_logger.log_data_info(df, "processed_data_final")
        debug_mode.add_debug_info("processed_data_shape", df.shape)
        
        # Log successful completion
        structured_logger.log_operation_end(operation_id, success=True, final_rows=len(df))
        structured_logger.log_user_action("data_loaded_successfully", rows=len(df), use_sample=use_sample)
        
        st.success(f"Successfully loaded and processed {len(df)} records!")
        return df
        
    except (DataLoadingError, DataProcessingError, DataValidationError, InsufficientMemoryError) as e:
        structured_logger.log_operation_end(operation_id, success=False, error=str(e))
        structured_logger.log_error_with_context(e, "Data Loading and Processing")
        
        global_error_handler.handle_error(
            error=e,
            context="Data Loading and Processing",
            user_message=None,  # Let error handler generate appropriate message
            recovery_suggestions=[
                "Try using the sample data option",
                "Verify your data file format",
                "Check available system memory"
            ]
        )
        
        # Display error report form
        error_reporting.display_error_report_form(e, "Data Loading and Processing")
        return None
        
    except Exception as e:
        structured_logger.log_operation_end(operation_id, success=False, error=str(e))
        structured_logger.log_error_with_context(e, "Data Loading and Processing")
        
        global_error_handler.handle_error(
            error=e,
            context="Data Loading and Processing",
            user_message="An unexpected error occurred while loading your data.",
            recovery_suggestions=[
                "Try refreshing the page",
                "Use the sample data option",
                "Verify your file is a valid CORD-19 metadata.csv"
            ]
        )
        
        # Display error report form
        error_reporting.display_error_report_form(e, "Data Loading and Processing")
        return None


@safe_execute(
    context="Data Filtering",
    user_message="Filter application failed. Showing unfiltered data.",
    fallback_value=None
)
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply user-selected filters to the dataset with error handling."""
    if df is None or df.empty:
        return df
        
    try:
        filtered_df = df.copy()
        
        # Apply date range filter
        if 'date_range' in st.session_state and 'publication_year' in filtered_df.columns:
            min_year, max_year = st.session_state.date_range
            filtered_df = filtered_df[
                (filtered_df['publication_year'] >= min_year) & 
                (filtered_df['publication_year'] <= max_year)
            ]
        
        # Apply journal filter
        if 'selected_journals' in st.session_state and st.session_state.selected_journals:
            if 'journal' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['journal'].isin(st.session_state.selected_journals)]
        
        # Apply source filter
        if 'selected_sources' in st.session_state and st.session_state.selected_sources:
            source_col = 'source_x' if 'source_x' in filtered_df.columns else 'source'
            if source_col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[source_col].isin(st.session_state.selected_sources)]
        
        # Show filter results
        if len(filtered_df) != len(df):
            st.info(f"Showing {len(filtered_df)} of {len(df)} records after applying filters")
        
        return filtered_df
        
    except Exception as e:
        global_error_handler.handle_error(
            error=e,
            context="Data Filtering",
            user_message="Filter application failed. Showing unfiltered data.",
            recovery_suggestions=[
                "Try clearing your filter selections",
                "Refresh the page to reset filters",
                "Check your data for compatibility issues"
            ]
        )
        return df  # Return original data if filtering fails


@create_error_boundary("Temporal Analysis")
@debug_function_decorator
def display_temporal_analysis(df: pd.DataFrame):
    """Display temporal trends analysis with comprehensive error handling and logging."""
    operation_id = structured_logger.log_operation_start("temporal_analysis", data_rows=len(df))
    
    # Monitor memory before analysis
    memory_monitor = MemoryMonitor()
    memory_monitor.display_memory_warning()
    
    try:
        with progress_tracker("Analyzing temporal trends", total_steps=3) as tracker:
            tracker.update(1, "Processing publication dates...")
            temporal_results = analyze_temporal_trends(df)
            
            tracker.update(2, "Creating visualizations...")
            if temporal_results['papers_by_year']:
                # Create and display temporal plot
                fig = create_temporal_plot(temporal_results['papers_by_year'])
                fig = add_interactive_features(fig)
                fig = create_responsive_layout(fig)
                
                tracker.update(3, "Rendering charts...")
                st.plotly_chart(fig, use_container_width=True)
                
                # Display summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Papers with Dates", temporal_results['total_papers_with_dates'])
                with col2:
                    st.metric("Peak Year", temporal_results['peak_year'])
                with col3:
                    date_range = temporal_results['date_range']
                    st.metric("Year Range", f"{date_range[0]} - {date_range[1]}")
                
                st.info(temporal_results['trend_summary'])
                
                # Log successful analysis
                structured_logger.log_operation_end(operation_id, success=True, 
                                                  papers_analyzed=temporal_results['total_papers_with_dates'])
                structured_logger.log_user_action("temporal_analysis_completed", 
                                                papers_with_dates=temporal_results['total_papers_with_dates'])
            else:
                st.warning("No temporal data available for analysis")
                structured_logger.log_operation_end(operation_id, success=False, reason="no_temporal_data")
        
            
    except AnalysisError as e:
        structured_logger.log_operation_end(operation_id, success=False, error=str(e))
        structured_logger.log_error_with_context(e, "Temporal Analysis")
        
        global_error_handler.handle_error(
            error=e,
            context="Temporal Analysis",
            recovery_suggestions=[
                "Check if your data contains valid publication dates",
                "Try using a different date range filter",
                "Verify your data file format"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Temporal analysis unavailable")
        
    except Exception as e:
        structured_logger.log_operation_end(operation_id, success=False, error=str(e))
        structured_logger.log_error_with_context(e, "Temporal Analysis")
        
        global_error_handler.handle_error(
            error=e,
            context="Temporal Analysis",
            user_message="Temporal analysis could not be completed.",
            recovery_suggestions=[
                "Try refreshing the page",
                "Check your data for date information",
                "Use the sample data to test functionality"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Temporal analysis failed")


@create_error_boundary("Journal Analysis")
def display_journal_analysis(df: pd.DataFrame):
    """Display journal analysis with comprehensive error handling."""
    # Monitor memory before analysis
    memory_monitor = MemoryMonitor()
    memory_monitor.display_memory_warning()
    
    try:
        with progress_tracker("Analyzing journals", total_steps=3) as tracker:
            tracker.update(1, "Processing journal data...")
            top_n = st.session_state.get('top_journals_n', 10)
            top_journals = get_top_journals(df, n=top_n)
            
            tracker.update(2, "Creating visualizations...")
            if not top_journals.empty:
                # Create and display journal bar chart
                fig = create_journal_bar_chart(top_journals, top_n=top_n)
                fig = add_interactive_features(fig)
                fig = create_responsive_layout(fig)
                
                tracker.update(3, "Rendering charts...")
                st.plotly_chart(fig, use_container_width=True)
                
                # Display top journals table
                st.subheader("Top Journals Table")
                journal_df = pd.DataFrame({
                    'Journal': top_journals.index,
                    'Publications': top_journals.values,
                    'Percentage': (top_journals.values / len(df) * 100).round(2)
                })
                st.dataframe(journal_df, use_container_width=True)
            else:
                st.warning("No journal data available for analysis")

            
    except AnalysisError as e:
        global_error_handler.handle_error(
            error=e,
            context="Journal Analysis",
            recovery_suggestions=[
                "Check if your data contains journal information",
                "Verify the journal column format",
                "Try using different filter settings"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Journal analysis unavailable")
        
    except Exception as e:
        global_error_handler.handle_error(
            error=e,
            context="Journal Analysis",
            user_message="Journal analysis could not be completed.",
            recovery_suggestions=[
                "Try refreshing the page",
                "Check your data for journal information",
                "Use the sample data to test functionality"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Journal analysis failed")


@create_error_boundary("Source Analysis")
def display_source_analysis(df: pd.DataFrame):
    """Display source distribution analysis with comprehensive error handling."""
    try:
        source_dist = calculate_source_distribution(df)
        
        if not source_dist.empty:
            # Chart type selection
            chart_type = st.radio("Chart Type", ["pie", "bar"], horizontal=True)
            
            # Create and display distribution chart
            fig = create_distribution_chart(source_dist, chart_type=chart_type)
            fig = add_interactive_features(fig)
            fig = create_responsive_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display source distribution table
            st.subheader("Source Distribution Table")
            source_df = pd.DataFrame({
                'Source': source_dist.index,
                'Publications': source_dist.values,
                'Percentage': (source_dist.values / len(df) * 100).round(2)
            })
            st.dataframe(source_df, use_container_width=True)
        else:
            st.warning("No source data available for analysis")
            
    except AnalysisError as e:
        global_error_handler.handle_error(
            error=e,
            context="Source Analysis",
            recovery_suggestions=[
                "Check if your data contains source information",
                "Verify the source column format",
                "Try using different filter settings"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Source analysis unavailable")
        
    except Exception as e:
        global_error_handler.handle_error(
            error=e,
            context="Source Analysis",
            user_message="Source analysis could not be completed.",
            recovery_suggestions=[
                "Try refreshing the page",
                "Check your data for source information",
                "Use the sample data to test functionality"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Source analysis failed")


@create_error_boundary("Content Analysis")
def display_content_analysis(df: pd.DataFrame):
    """Display content and keyword analysis with comprehensive error handling."""
    # Monitor memory before analysis
    memory_monitor = MemoryMonitor()
    memory_monitor.display_memory_warning()
    
    try:
        with progress_tracker("Analyzing content", total_steps=4) as tracker:
            tracker.update(1, "Extracting keywords from titles...")
            top_n = st.session_state.get('top_keywords_n', 100)
            keywords = extract_title_keywords(df, n=top_n)
            
            tracker.update(2, "Processing text data...")
            if keywords:
                # Generate and display word cloud
                st.subheader("Title Keywords Word Cloud")
                try:
                    tracker.update(3, "Generating word cloud...")
                    word_cloud_img = generate_word_cloud(keywords)
                    st.image(word_cloud_img, use_column_width=True)
                except Exception as e:
                    st.warning(f"Could not generate word cloud: {str(e)}")
                
                tracker.update(4, "Creating summary tables...")
                # Display top keywords table
                st.subheader("Top Keywords Table")
                keywords_df = pd.DataFrame({
                    'Keyword': list(keywords.keys())[:20],  # Show top 20 in table
                    'Frequency': list(keywords.values())[:20]
                })
                st.dataframe(keywords_df, use_container_width=True)
                
                # Content statistics
                if 'abstract_word_count' in df.columns:
                    col1, col2 = st.columns(2)
                    with col1:
                        avg_abstract_words = df['abstract_word_count'].mean()
                        st.metric("Avg Abstract Words", f"{avg_abstract_words:.1f}")
                    with col2:
                        if 'title_word_count' in df.columns:
                            avg_title_words = df['title_word_count'].mean()
                            st.metric("Avg Title Words", f"{avg_title_words:.1f}")
            else:
                st.warning("No keywords could be extracted from titles")

            
    except AnalysisError as e:
        global_error_handler.handle_error(
            error=e,
            context="Content Analysis",
            recovery_suggestions=[
                "Check if your data contains title information",
                "Verify the title column format",
                "Try reducing the number of keywords"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Content analysis unavailable")
        
    except Exception as e:
        global_error_handler.handle_error(
            error=e,
            context="Content Analysis",
            user_message="Content analysis could not be completed.",
            recovery_suggestions=[
                "Try refreshing the page",
                "Check your data for title information",
                "Use the sample data to test functionality"
            ]
        )
        GracefulDegradation.fallback_analysis_display("Content analysis failed")


@create_error_boundary("Data Overview")
def display_data_overview(df: pd.DataFrame):
    """Display data overview and sample viewing with comprehensive error handling."""
    # Data summary statistics
    st.subheader("📊 Dataset Summary")
    
    try:
        summary = get_analysis_summary(df)
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Papers", summary['dataset_overview']['total_papers'])
        with col2:
            st.metric("Total Columns", summary['dataset_overview']['total_columns'])
        with col3:
            if 'temporal_analysis' in summary and 'papers_with_dates' in summary['temporal_analysis']:
                st.metric("Papers with Dates", summary['temporal_analysis']['papers_with_dates'])
        with col4:
            if 'journal_analysis' in summary and 'total_unique_journals' in summary['journal_analysis']:
                st.metric("Unique Journals", summary['journal_analysis']['total_unique_journals'])
        
        # Data coverage information
        st.subheader("📈 Data Coverage")
        coverage_data = []
        for key, value in summary['dataset_overview'].items():
            if key.endswith('_coverage') and isinstance(value, dict):
                field_name = key.replace('_coverage', '').replace('_', ' ').title()
                coverage_data.append({
                    'Field': field_name,
                    'Records': value['count'],
                    'Coverage %': value['percentage']
                })
        
        if coverage_data:
            coverage_df = pd.DataFrame(coverage_data)
            st.dataframe(coverage_df, use_container_width=True)
        
    except Exception as e:
        st.warning(f"Could not generate full summary: {str(e)}")
        # Fallback to basic summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Total Columns", len(df.columns))
    
    # Sample data viewer with filtering options
    st.subheader("🔍 Data Sample Viewer")
    
    # Filtering options for sample viewer
    col1, col2 = st.columns(2)
    with col1:
        # Column selection
        available_columns = list(df.columns)
        selected_columns = st.multiselect(
            "Select columns to display",
            options=available_columns,
            default=available_columns[:6] if len(available_columns) > 6 else available_columns,
            help="Choose which columns to show in the data table"
        )
    
    with col2:
        # Sample size selection
        sample_size = st.number_input(
            "Number of rows to display",
            min_value=10,
            max_value=min(1000, len(df)),
            value=min(50, len(df)),
            step=10,
            help="Select how many rows to display"
        )
    
    # Display filtered sample data
    if selected_columns:
        sample_df = df[selected_columns].head(sample_size)
        
        # Add search functionality
        search_term = st.text_input(
            "Search in displayed data",
            help="Enter a term to search across all displayed columns"
        )
        
        if search_term:
            # Filter sample data based on search term
            mask = sample_df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            sample_df = sample_df[mask]
            
            if len(sample_df) == 0:
                st.warning(f"No results found for '{search_term}'")
            else:
                st.info(f"Found {len(sample_df)} rows matching '{search_term}'")
        
        # Display the data table with pagination-like functionality
        if not sample_df.empty:
            st.dataframe(
                sample_df,
                use_container_width=True,
                height=400
            )
            
            # Download option
            csv = sample_df.to_csv(index=False)
            st.download_button(
                label="📥 Download displayed data as CSV",
                data=csv,
                file_name="covid_research_sample.csv",
                mime="text/csv"
            )
        else:
            st.info("No data to display with current filters")
    else:
        st.warning("Please select at least one column to display")
    
    # Data quality information
    st.subheader("🔍 Data Quality Overview")
    
    # Missing values summary
    missing_data = df.isnull().sum()
    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
    
    if not missing_data.empty:
        st.write("**Missing Values by Column:**")
        missing_df = pd.DataFrame({
            'Column': missing_data.index,
            'Missing Count': missing_data.values,
            'Missing %': (missing_data.values / len(df) * 100).round(2)
        })
        st.dataframe(missing_df, use_container_width=True)
    else:
        st.success("✅ No missing values detected in the dataset")


if __name__ == "__main__":
    main()

# Health check endpoints for deployment
def setup_health_endpoints():
    """Set up health check endpoints for the application."""
    # This would typically be handled by a web framework
    # For Streamlit, we can add query parameter handling
    
    # Check if this is a health check request
    try:
        query_params = st.query_params
    except AttributeError:
        # Fallback for older Streamlit versions
        query_params = st.experimental_get_query_params()
    
    if 'health' in query_params:
        health_type = query_params.get('health', [''])[0]
        
        if health_type == 'ready':
            status = get_readiness_status()
        elif health_type == 'live':
            from health_check import get_liveness_status
            status = get_liveness_status()
        else:
            status = get_health_status()
        
        # Display health status as JSON
        st.json(status)
        st.stop()  # Stop further execution for health checks


# Call health endpoint setup
try:
    setup_health_endpoints()
except:
    # Ignore errors in health endpoint setup to not break main app
    pass


# Add configuration info to sidebar if debug mode is enabled
def add_debug_info_to_sidebar():
    """Add debug information to sidebar if enabled."""
    if app_config.show_debug_info and app_config.debug_mode:
        with st.sidebar:
            st.markdown("---")
            st.subheader("🔧 Configuration Info")
            
            with st.expander("App Config"):
                config_dict = {
                    'Environment': app_config.environment,
                    'Debug Mode': app_config.debug_mode,
                    'Log Level': app_config.log_level,
                    'Caching Enabled': app_config.enable_caching,
                    'Sampling Enabled': app_config.enable_sampling,
                    'Max File Size (MB)': app_config.max_file_size_mb,
                }
                
                for key, value in config_dict.items():
                    st.write(f"**{key}:** {value}")
            
            with st.expander("System Health"):
                if st.button("Check System Health"):
                    health_status = get_health_status()
                    st.json(health_status)


# Add debug info if enabled
add_debug_info_to_sidebar()