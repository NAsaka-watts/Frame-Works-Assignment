"""
Visualization component for COVID-19 Research Analyzer.

This module provides functions to create interactive visualizations
using Plotly for temporal trends, journal rankings, and source distributions.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, Optional
import logging
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_temporal_plot(temporal_data: Dict[int, int], 
                        title: str = "COVID-19 Research Publications Over Time") -> go.Figure:
    """
    Create an interactive line chart showing publication counts over time.
    
    Args:
        temporal_data: Dictionary with years as keys and publication counts as values
        title: Chart title
        
    Returns:
        Plotly Figure object with interactive line chart
        
    Raises:
        ValueError: If temporal_data is empty or invalid
    """
    try:
        if not temporal_data:
            raise ValueError("Temporal data cannot be empty")
            
        # Convert dictionary to DataFrame for easier plotting
        df = pd.DataFrame(list(temporal_data.items()), columns=['Year', 'Publications'])
        df = df.sort_values('Year')
        
        # Create interactive line plot
        fig = px.line(
            df, 
            x='Year', 
            y='Publications',
            title=title,
            markers=True,
            hover_data={'Year': True, 'Publications': True}
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title="Publication Year",
            yaxis_title="Number of Publications",
            hovermode='x unified',
            showlegend=False,
            template='plotly_white',
            height=500
        )
        
        # Add hover information
        fig.update_traces(
            hovertemplate="<b>Year:</b> %{x}<br><b>Publications:</b> %{y}<extra></extra>",
            line=dict(width=3)
        )
        
        logger.info(f"Created temporal plot with {len(df)} data points")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating temporal plot: {str(e)}")
        raise


def create_journal_bar_chart(journal_data: pd.Series, 
                           top_n: int = 10,
                           title: str = "Top Journals Publishing COVID-19 Research") -> go.Figure:
    """
    Create a horizontal bar chart showing top journals by publication count.
    
    Args:
        journal_data: Pandas Series with journal names as index and counts as values
        top_n: Number of top journals to display
        title: Chart title
        
    Returns:
        Plotly Figure object with horizontal bar chart
        
    Raises:
        ValueError: If journal_data is empty or invalid
    """
    try:
        if journal_data.empty:
            raise ValueError("Journal data cannot be empty")
            
        # Get top N journals
        top_journals = journal_data.head(top_n)
        
        # Create horizontal bar chart
        fig = px.bar(
            x=top_journals.values,
            y=top_journals.index,
            orientation='h',
            title=title,
            labels={'x': 'Number of Publications', 'y': 'Journal'}
        )
        
        # Customize layout
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            template='plotly_white',
            height=max(400, top_n * 40),  # Dynamic height based on number of journals
            margin=dict(l=200)  # Left margin for journal names
        )
        
        # Add hover information
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>Publications: %{x}<extra></extra>",
            marker_color='steelblue'
        )
        
        logger.info(f"Created journal bar chart with top {len(top_journals)} journals")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating journal bar chart: {str(e)}")
        raise


def create_distribution_chart(distribution_data: pd.Series,
                            chart_type: str = "pie",
                            title: str = "Distribution of Papers by Source") -> go.Figure:
    """
    Create a chart showing distribution of papers by source.
    
    Args:
        distribution_data: Pandas Series with source names as index and counts as values
        chart_type: Type of chart ('pie' or 'bar')
        title: Chart title
        
    Returns:
        Plotly Figure object with distribution chart
        
    Raises:
        ValueError: If distribution_data is empty or chart_type is invalid
    """
    try:
        if distribution_data.empty:
            raise ValueError("Distribution data cannot be empty")
            
        if chart_type not in ['pie', 'bar']:
            raise ValueError("Chart type must be 'pie' or 'bar'")
        
        if chart_type == 'pie':
            # Create pie chart
            fig = px.pie(
                values=distribution_data.values,
                names=distribution_data.index,
                title=title
            )
            
            # Customize pie chart
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>Papers: %{value}<br>Percentage: %{percent}<extra></extra>",
                textposition='inside',
                textinfo='percent+label'
            )
            
        else:  # bar chart
            # Create vertical bar chart
            fig = px.bar(
                x=distribution_data.index,
                y=distribution_data.values,
                title=title,
                labels={'x': 'Source', 'y': 'Number of Papers'}
            )
            
            # Customize bar chart
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>Papers: %{y}<extra></extra>",
                marker_color='lightcoral'
            )
        
        # Common layout updates
        fig.update_layout(
            template='plotly_white',
            height=500,
            showlegend=(chart_type == 'pie')
        )
        
        logger.info(f"Created {chart_type} distribution chart with {len(distribution_data)} categories")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating distribution chart: {str(e)}")
        raise


def create_summary_stats_table(stats_data: Dict[str, Any]) -> go.Figure:
    """
    Create a table displaying summary statistics.
    
    Args:
        stats_data: Dictionary containing summary statistics
        
    Returns:
        Plotly Figure object with table
    """
    try:
        if not stats_data:
            raise ValueError("Stats data cannot be empty")
        
        # Prepare data for table
        metrics = list(stats_data.keys())
        values = [str(v) for v in stats_data.values()]
        
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Metric', 'Value'],
                fill_color='lightblue',
                align='left',
                font=dict(size=14, color='black')
            ),
            cells=dict(
                values=[metrics, values],
                fill_color='white',
                align='left',
                font=dict(size=12)
            )
        )])
        
        fig.update_layout(
            title="Dataset Summary Statistics",
            height=min(400, len(metrics) * 40 + 100),
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        logger.info(f"Created summary stats table with {len(metrics)} metrics")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating summary stats table: {str(e)}")
        raise


# Advanced visualization features for Task 5.2


def generate_word_cloud(word_freq: Dict[str, int], 
                       width: int = 800, 
                       height: int = 400,
                       background_color: str = 'white',
                       max_words: int = 100) -> Image.Image:
    """
    Generate a word cloud from title keywords.
    Implementation for task 5.2 requirement: "Implement generate_word_cloud() for title keyword visualization"
    
    Args:
        word_freq: Dictionary with words as keys and frequencies as values
        width: Width of the word cloud image
        height: Height of the word cloud image
        background_color: Background color for the word cloud
        max_words: Maximum number of words to display
        
    Returns:
        PIL Image object containing the word cloud
        
    Raises:
        ValueError: If word_freq is empty or invalid
    """
    try:
        if not word_freq:
            raise ValueError("Word frequency data cannot be empty")
        
        # Create WordCloud object
        wordcloud = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            max_words=max_words,
            colormap='viridis',
            relative_scaling=0.5,
            random_state=42
        ).generate_from_frequencies(word_freq)
        
        # Convert to PIL Image
        image = wordcloud.to_image()
        
        logger.info(f"Generated word cloud with {len(word_freq)} words")
        return image
        
    except Exception as e:
        logger.error(f"Error generating word cloud: {str(e)}")
        raise


def create_responsive_layout(fig: go.Figure, mobile_breakpoint: int = 768) -> go.Figure:
    """
    Create responsive chart layouts for different screen sizes.
    Implementation for task 5.2 requirement: "Create responsive chart layouts for different screen sizes"
    
    Args:
        fig: Plotly figure to make responsive
        mobile_breakpoint: Screen width threshold for mobile layout
        
    Returns:
        Modified Plotly figure with responsive layout
    """
    try:
        # Update layout for responsiveness
        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50),
            font=dict(size=12)
        )
        
        # Add mobile-friendly settings
        fig.update_xaxes(
            tickangle=45,
            tickfont=dict(size=10)
        )
        
        fig.update_yaxes(
            tickfont=dict(size=10)
        )
        
        logger.info("Applied responsive layout to figure")
        return fig
        
    except Exception as e:
        logger.error(f"Error creating responsive layout: {str(e)}")
        raise


def add_interactive_features(fig: go.Figure, 
                           enable_zoom: bool = True,
                           enable_hover: bool = True,
                           enable_selection: bool = True) -> go.Figure:
    """
    Add interactive features like hover information and zoom to charts.
    Implementation for task 5.2 requirement: "Add interactive features like hover information and zoom"
    
    Args:
        fig: Plotly figure to enhance
        enable_zoom: Whether to enable zoom functionality
        enable_hover: Whether to enable hover information
        enable_selection: Whether to enable data selection
        
    Returns:
        Enhanced Plotly figure with interactive features
    """
    try:
        # Update layout with interactive features
        fig.update_layout(
            hovermode='closest' if enable_hover else False,
            dragmode='zoom' if enable_zoom else 'pan'
        )
        
        # Enhanced hover templates for better user experience
        if enable_hover:
            for trace in fig.data:
                if hasattr(trace, 'hovertemplate') and not trace.hovertemplate:
                    trace.hovertemplate = "<b>%{x}</b><br>Value: %{y}<extra></extra>"
        
        logger.info("Added interactive features to figure")
        return fig
        
    except Exception as e:
        logger.error(f"Error adding interactive features: {str(e)}")
        raise