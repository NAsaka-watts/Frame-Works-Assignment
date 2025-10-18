"""
Health check module for COVID-19 Research Analyzer.

This module provides health check endpoints and system monitoring capabilities.
"""

import time
import psutil
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check and system monitoring class."""
    
    def __init__(self):
        """Initialize health checker."""
        self.start_time = datetime.now()
        self.check_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health information.
        
        Returns:
            Dict[str, Any]: System health status and metrics
        """
        try:
            # Basic system information
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'checks': {}
            }
            
            # Memory check
            memory_check = self._check_memory()
            health_status['checks']['memory'] = memory_check
            
            # CPU check
            cpu_check = self._check_cpu()
            health_status['checks']['cpu'] = cpu_check
            
            # Disk check
            disk_check = self._check_disk()
            health_status['checks']['disk'] = disk_check
            
            # Python environment check
            python_check = self._check_python_environment()
            health_status['checks']['python'] = python_check
            
            # Dependencies check
            deps_check = self._check_dependencies()
            health_status['checks']['dependencies'] = deps_check
            
            # Application components check
            components_check = self._check_application_components()
            health_status['checks']['components'] = components_check
            
            # Determine overall health status
            failed_checks = [
                check_name for check_name, check_result in health_status['checks'].items()
                if check_result['status'] != 'healthy'
            ]
            
            if failed_checks:
                health_status['status'] = 'degraded' if len(failed_checks) <= 2 else 'unhealthy'
                health_status['failed_checks'] = failed_checks
            
            # Store in history
            self._store_check_result(health_status)
            
            logger.info(f"Health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'checks': {}
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            
            status = 'healthy'
            if memory.percent > 90:
                status = 'critical'
            elif memory.percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': memory.percent,
                'message': f"Memory usage: {memory.percent:.1f}%"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check memory'
            }
    
    def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            status = 'healthy'
            if cpu_percent > 90:
                status = 'critical'
            elif cpu_percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'cpu_count': cpu_count,
                'cpu_percent': cpu_percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'message': f"CPU usage: {cpu_percent:.1f}%"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check CPU'
            }
    
    def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage('/')
            
            status = 'healthy'
            if disk.percent > 95:
                status = 'critical'
            elif disk.percent > 85:
                status = 'warning'
            
            return {
                'status': status,
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_percent': disk.percent,
                'message': f"Disk usage: {disk.percent:.1f}%"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check disk'
            }
    
    def _check_python_environment(self) -> Dict[str, Any]:
        """Check Python environment."""
        try:
            return {
                'status': 'healthy',
                'python_version': sys.version,
                'python_executable': sys.executable,
                'platform': sys.platform,
                'message': f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check Python environment'
            }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies."""
        try:
            critical_modules = [
                'streamlit',
                'pandas',
                'plotly',
                'wordcloud',
                'psutil'
            ]
            
            missing_modules = []
            module_versions = {}
            
            for module in critical_modules:
                try:
                    imported_module = __import__(module)
                    version = getattr(imported_module, '__version__', 'unknown')
                    module_versions[module] = version
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                return {
                    'status': 'critical',
                    'missing_modules': missing_modules,
                    'available_modules': module_versions,
                    'message': f"Missing critical modules: {', '.join(missing_modules)}"
                }
            
            return {
                'status': 'healthy',
                'modules': module_versions,
                'message': f"All {len(critical_modules)} critical modules available"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check dependencies'
            }
    
    def _check_application_components(self) -> Dict[str, Any]:
        """Check application components."""
        try:
            components_status = {}
            
            # Check data loader
            try:
                from data_loader import load_metadata, get_data_summary
                components_status['data_loader'] = 'healthy'
            except Exception as e:
                components_status['data_loader'] = f'error: {e}'
            
            # Check data processor
            try:
                from data_processor import clean_missing_values, process_dates
                components_status['data_processor'] = 'healthy'
            except Exception as e:
                components_status['data_processor'] = f'error: {e}'
            
            # Check analyzer
            try:
                from analyzer import analyze_temporal_trends, get_top_journals
                components_status['analyzer'] = 'healthy'
            except Exception as e:
                components_status['analyzer'] = f'error: {e}'
            
            # Check visualizer
            try:
                from visualizer import create_temporal_plot, generate_word_cloud
                components_status['visualizer'] = 'healthy'
            except Exception as e:
                components_status['visualizer'] = f'error: {e}'
            
            # Check error handling
            try:
                from error_handler import global_error_handler
                components_status['error_handler'] = 'healthy'
            except Exception as e:
                components_status['error_handler'] = f'error: {e}'
            
            # Determine overall component health
            failed_components = [
                comp for comp, status in components_status.items()
                if status != 'healthy'
            ]
            
            overall_status = 'healthy' if not failed_components else 'degraded'
            
            return {
                'status': overall_status,
                'components': components_status,
                'failed_components': failed_components,
                'message': f"Components status: {len(components_status) - len(failed_components)}/{len(components_status)} healthy"
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to check application components'
            }
    
    def _store_check_result(self, result: Dict[str, Any]) -> None:
        """Store health check result in history."""
        self.check_history.append(result)
        
        # Keep only recent history
        if len(self.check_history) > self.max_history_size:
            self.check_history = self.check_history[-self.max_history_size:]
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health check history for the specified time period.
        
        Args:
            hours (int): Number of hours of history to return
            
        Returns:
            List[Dict[str, Any]]: List of health check results
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            check for check in self.check_history
            if datetime.fromisoformat(check['timestamp']) > cutoff_time
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recent health status.
        
        Returns:
            Dict[str, Any]: Health summary statistics
        """
        if not self.check_history:
            return {'message': 'No health check history available'}
        
        recent_checks = self.get_health_history(hours=1)
        if not recent_checks:
            recent_checks = self.check_history[-10:]  # Last 10 checks
        
        status_counts = {}
        for check in recent_checks:
            status = check.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        latest_check = self.check_history[-1]
        
        return {
            'current_status': latest_check.get('status', 'unknown'),
            'uptime_hours': round((datetime.now() - self.start_time).total_seconds() / 3600, 2),
            'total_checks': len(self.check_history),
            'recent_checks': len(recent_checks),
            'status_distribution': status_counts,
            'last_check_time': latest_check.get('timestamp'),
            'message': f"System running for {round((datetime.now() - self.start_time).total_seconds() / 3600, 1)} hours"
        }


# Global health checker instance
health_checker = HealthChecker()


def get_health_status() -> Dict[str, Any]:
    """
    Get current health status (convenience function).
    
    Returns:
        Dict[str, Any]: Current health status
    """
    return health_checker.get_system_health()


def get_readiness_status() -> Dict[str, Any]:
    """
    Get readiness status for load balancer health checks.
    
    Returns:
        Dict[str, Any]: Readiness status
    """
    try:
        # Quick readiness checks
        health_status = health_checker.get_system_health()
        
        # Check if critical components are working
        critical_checks = ['dependencies', 'components']
        critical_failures = [
            check for check in critical_checks
            if health_status['checks'].get(check, {}).get('status') not in ['healthy', 'warning']
        ]
        
        if critical_failures:
            return {
                'status': 'not_ready',
                'timestamp': datetime.now().isoformat(),
                'failed_checks': critical_failures,
                'message': 'Critical components not ready'
            }
        
        return {
            'status': 'ready',
            'timestamp': datetime.now().isoformat(),
            'message': 'Application ready to serve requests'
        }
        
    except Exception as e:
        return {
            'status': 'not_ready',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'message': 'Readiness check failed'
        }


def get_liveness_status() -> Dict[str, Any]:
    """
    Get liveness status for container orchestration.
    
    Returns:
        Dict[str, Any]: Liveness status
    """
    try:
        # Simple liveness check - just verify the application is running
        return {
            'status': 'alive',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - health_checker.start_time).total_seconds(),
            'message': 'Application is alive and responding'
        }
        
    except Exception as e:
        return {
            'status': 'dead',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'message': 'Liveness check failed'
        }


def create_health_check_endpoints():
    """
    Create health check endpoints for web frameworks.
    This function can be used to set up health check routes.
    """
    endpoints = {
        '/health': get_health_status,
        '/health/ready': get_readiness_status,
        '/health/live': get_liveness_status,
        '/health/summary': lambda: health_checker.get_health_summary(),
        '/health/history': lambda: health_checker.get_health_history()
    }
    
    return endpoints