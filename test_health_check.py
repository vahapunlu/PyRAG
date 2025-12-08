"""
Test Health Check & System Monitoring
"""

import sys
import time
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.health_check import HealthCheck, HealthStatus


def test_health_check():
    """Test health check system"""
    logger.info("=" * 60)
    logger.info("Testing Health Check")
    logger.info("=" * 60)
    
    health = HealthCheck()
    
    # Test 1: Register components
    logger.info("\n📝 Test 1: Registering components...")
    
    # Healthy component
    def check_database():
        return True
    
    # Degraded component
    unhealthy_count = {'value': 0}
    def check_api():
        unhealthy_count['value'] += 1
        return unhealthy_count['value'] <= 2  # Fail after 2 calls
    
    # Failing component
    def check_network():
        return False
    
    health.register_component('database', check_database)
    health.register_component('api', check_api)
    health.register_component('network', check_network)
    
    logger.success("✅ Components registered: database, api, network")
    
    # Test 2: Check individual components
    logger.info("\n🔍 Test 2: Checking individual components...")
    
    db_status = health.check_component('database', force=True)
    logger.info(f"Database status: {db_status.value}")
    
    api_status = health.check_component('api', force=True)
    logger.info(f"API status: {api_status.value}")
    
    net_status = health.check_component('network', force=True)
    logger.info(f"Network status: {net_status.value}")
    
    # Test 3: System health report
    logger.info("\n📊 Test 3: System health report...")
    
    report = health.get_system_health()
    logger.info(f"Overall status: {report['overall_status'].value}")
    logger.info(f"Summary: {report['summary']}")
    
    for comp_name, comp_data in report['components'].items():
        logger.info(f"  - {comp_name}: {comp_data['status']} "
                   f"(failures: {comp_data['failures']}, "
                   f"successes: {comp_data['success_count']})")
    
    # Test 4: Trigger degradation
    logger.info("\n⚠️ Test 4: Triggering degradation...")
    
    for i in range(3):
        status = health.check_component('api', force=True)
        logger.info(f"  API check {i+1}: {status.value}")
    
    # Check final report
    final_report = health.get_system_health()
    logger.info(f"Final overall status: {final_report['overall_status'].value}")
    
    # Test 5: Unhealthy components list
    logger.info("\n❌ Test 5: Unhealthy components...")
    
    unhealthy = health.get_unhealthy_components()
    if unhealthy:
        logger.warning(f"Unhealthy components: {unhealthy}")
    else:
        logger.success("✅ No unhealthy components")
    
    # Test 6: Quick health check
    logger.info("\n✅ Test 6: Quick health checks...")
    
    is_db_healthy = health.is_component_healthy('database')
    is_api_healthy = health.is_component_healthy('api')
    is_net_healthy = health.is_component_healthy('network')
    
    logger.info(f"Database healthy: {is_db_healthy}")
    logger.info(f"API healthy: {is_api_healthy}")
    logger.info(f"Network healthy: {is_net_healthy}")
    
    logger.info("\n" + "=" * 60)
    logger.success("✅ All health check tests completed!")


def test_component_recovery():
    """Test component recovery after failure"""
    logger.info("\n" + "=" * 60)
    logger.info("Test Component Recovery")
    logger.info("=" * 60)
    
    health = HealthCheck()
    
    # Simulated recovering component
    failure_count = {'value': 3}  # Start with failures
    
    def check_recovering_service():
        failure_count['value'] -= 1
        is_ok = failure_count['value'] <= 0
        logger.info(f"  Service check (failures left: {max(0, failure_count['value'])}): {'OK' if is_ok else 'FAIL'}")
        return is_ok
    
    health.register_component('recovering_service', check_recovering_service)
    
    # Initial checks (failing)
    logger.info("\n📉 Initial state (failing)...")
    for i in range(2):
        status = health.check_component('recovering_service', force=True)
        logger.info(f"Check {i+1}: {status.value}")
        time.sleep(0.1)
    
    # Recovery checks
    logger.info("\n📈 Recovery phase...")
    for i in range(3):
        status = health.check_component('recovering_service', force=True)
        logger.info(f"Check {i+1}: {status.value}")
        if status == HealthStatus.HEALTHY:
            logger.success("✅ Service recovered!")
            break
        time.sleep(0.1)


def test_health_monitoring_interval():
    """Test health check interval"""
    logger.info("\n" + "=" * 60)
    logger.info("Test Health Check Interval")
    logger.info("=" * 60)
    
    health = HealthCheck()
    health.check_interval = 2  # 2 seconds
    
    check_count = {'value': 0}
    
    def counting_check():
        check_count['value'] += 1
        logger.info(f"  Check executed (count: {check_count['value']})")
        return True
    
    health.register_component('service', counting_check)
    
    # First check
    logger.info("\n1️⃣ First check (should execute)...")
    health.check_component('service', force=False)
    
    # Immediate second check (should skip)
    logger.info("\n2️⃣ Immediate second check (should skip)...")
    health.check_component('service', force=False)
    
    # Third check after interval
    logger.info("\n3️⃣ After interval (should execute)...")
    time.sleep(2.1)
    health.check_component('service', force=False)
    
    # Forced check (should always execute)
    logger.info("\n4️⃣ Forced check (should execute)...")
    health.check_component('service', force=True)
    
    logger.info(f"\nTotal checks executed: {check_count['value']}")
    logger.success("✅ Interval test completed!")


if __name__ == "__main__":
    test_health_check()
    test_component_recovery()
    test_health_monitoring_interval()
