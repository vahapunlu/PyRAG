"""
Health Check Manager

Monitor system health and component availability.
"""

import time
from typing import Dict, List
from enum import Enum
from loguru import logger


class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """
    System health monitoring
    
    Features:
    - Component health tracking
    - Dependency monitoring
    - Degraded mode detection
    - Health metrics
    """
    
    def __init__(self):
        """Initialize health check"""
        self.components = {}
        self.last_check = {}
        self.check_interval = 60  # seconds
        
        logger.info("✅ Health Check initialized")
    
    def register_component(self, name: str, check_func: callable = None):
        """
        Register component for health monitoring
        
        Args:
            name: Component name
            check_func: Health check function (returns bool)
        """
        self.components[name] = {
            'check_func': check_func,
            'status': HealthStatus.UNKNOWN,
            'last_check': 0,
            'failures': 0,
            'success_count': 0
        }
        logger.debug(f"Registered component: {name}")
    
    def check_component(self, name: str, force: bool = False) -> HealthStatus:
        """
        Check component health
        
        Args:
            name: Component name
            force: Force check even if recently checked
            
        Returns:
            Health status
        """
        if name not in self.components:
            logger.warning(f"Unknown component: {name}")
            return HealthStatus.UNKNOWN
        
        component = self.components[name]
        current_time = time.time()
        
        # Skip if recently checked (unless forced)
        if not force and (current_time - component['last_check']) < self.check_interval:
            return component['status']
        
        # Run health check
        if component['check_func']:
            try:
                is_healthy = component['check_func']()
                component['last_check'] = current_time
                
                if is_healthy:
                    component['status'] = HealthStatus.HEALTHY
                    component['success_count'] += 1
                    component['failures'] = 0  # Reset failure counter
                else:
                    component['failures'] += 1
                    if component['failures'] >= 3:
                        component['status'] = HealthStatus.UNHEALTHY
                    else:
                        component['status'] = HealthStatus.DEGRADED
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                component['failures'] += 1
                component['status'] = HealthStatus.UNHEALTHY
                component['last_check'] = current_time
        
        return component['status']
    
    def get_system_health(self) -> Dict:
        """
        Get overall system health
        
        Returns:
            Health report with all components
        """
        report = {
            'timestamp': time.time(),
            'overall_status': HealthStatus.HEALTHY,
            'components': {},
            'summary': {
                'healthy': 0,
                'degraded': 0,
                'unhealthy': 0,
                'unknown': 0
            }
        }
        
        # Check all components
        for name in self.components:
            status = self.check_component(name)
            report['components'][name] = {
                'status': status.value,
                'failures': self.components[name]['failures'],
                'success_count': self.components[name]['success_count']
            }
            
            # Update summary
            if status == HealthStatus.HEALTHY:
                report['summary']['healthy'] += 1
            elif status == HealthStatus.DEGRADED:
                report['summary']['degraded'] += 1
            elif status == HealthStatus.UNHEALTHY:
                report['summary']['unhealthy'] += 1
            else:
                report['summary']['unknown'] += 1
        
        # Determine overall status
        if report['summary']['unhealthy'] > 0:
            report['overall_status'] = HealthStatus.UNHEALTHY
        elif report['summary']['degraded'] > 0:
            report['overall_status'] = HealthStatus.DEGRADED
        elif report['summary']['unknown'] == len(self.components):
            report['overall_status'] = HealthStatus.UNKNOWN
        else:
            report['overall_status'] = HealthStatus.HEALTHY
        
        return report
    
    def is_component_healthy(self, name: str) -> bool:
        """Quick check if component is healthy"""
        status = self.check_component(name)
        return status == HealthStatus.HEALTHY
    
    def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components"""
        unhealthy = []
        for name, component in self.components.items():
            if component['status'] == HealthStatus.UNHEALTHY:
                unhealthy.append(name)
        return unhealthy


# Singleton instance
_health_check = None

def get_health_check() -> HealthCheck:
    """Get or create health check singleton"""
    global _health_check
    
    if _health_check is None:
        _health_check = HealthCheck()
    
    return _health_check
