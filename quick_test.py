#!/usr/bin/env python3
"""
Quick Hardware Test for Raspberry Pi
Tests essential hardware components without display initialization

This script tests:
1. GPIO availability
2. LED patterns
3. Buzzer patterns
4. Basic hardware notifier functionality

Run this for a quick hardware verification.
"""

import time
import sys
import os
import requests
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware_notifier import get_hardware_notifier, NotificationType, cleanup_hardware_notifier
from config import RESTAURANT_ID, SERVER_URL

def test_gpio():
    """Test GPIO availability"""
    print("🔧 Testing GPIO...")
    try:
        import RPi.GPIO as GPIO
        print("✅ RPi.GPIO available")
        return True
    except ImportError:
        print("❌ RPi.GPIO not available")
        return False

def test_basic_hardware():
    """Test basic hardware functionality"""
    print("🚀 Testing basic hardware...")
    try:
        # Create notifier in simulation mode first to test basic functionality
        notifier = get_hardware_notifier(simulation_mode=True)
        print("✅ Basic hardware notifier created")
        
        # Test notifications
        print("💡 Testing LED patterns...")
        success = notifier.notify(NotificationType.NEW_ORDER, priority=1)
        if success:
            print("✅ LED notification test passed")
        else:
            print("❌ LED notification test failed")
        
        # Cleanup
        cleanup_hardware_notifier()
        return True
        
    except Exception as e:
        print(f"❌ Basic hardware test failed: {e}")
        return False

def test_real_hardware():
    """Test real hardware with timeout"""
    print("🔌 Testing real hardware...")
    try:
        # Test with a timeout
        import threading
        
        notifier = None
        success = False
        
        def init_hardware():
            nonlocal notifier, success
            try:
                notifier = get_hardware_notifier(simulation_mode=False)
                success = True
            except Exception as e:
                print(f"   Error: {e}")
                success = False
        
        # Start in separate thread with timeout
        thread = threading.Thread(target=init_hardware)
        thread.daemon = True
        thread.start()
        thread.join(timeout=5)  # 5 second timeout
        
        if thread.is_alive():
            print("⚠️  Hardware initialization timed out")
            return False
        
        if success and notifier:
            print("✅ Real hardware initialized")
            
            # Test a quick notification
            print("🔊 Testing buzzer...")
            notifier.notify(NotificationType.ORDER_READY, priority=1)
            time.sleep(1)
            
            cleanup_hardware_notifier()
            return True
        else:
            print("❌ Real hardware initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Real hardware test failed: {e}")
        return False

def test_network():
    """Test network connectivity"""
    print("🌐 Testing network...")
    try:
        response = requests.get(f"{SERVER_URL}/api/orders", 
                              params={'restaurant_id': RESTAURANT_ID}, 
                              timeout=3)
        if response.status_code == 200:
            print("✅ Network connectivity OK")
            return True
        else:
            print(f"⚠️  Network responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Network test failed: {e}")
        return False

def main():
    """Run quick hardware test"""
    print("=" * 50)
    print("QUICK HARDWARE TEST")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    results = {}
    
    # Test 1: GPIO
    results['gpio'] = test_gpio()
    
    # Test 2: Basic Hardware
    results['basic'] = test_basic_hardware()
    
    # Test 3: Real Hardware
    results['real'] = test_real_hardware()
    
    # Test 4: Network
    results['network'] = test_network()
    
    # Summary
    print("\n" + "=" * 50)
    print("QUICK TEST SUMMARY")
    print("=" * 50)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test.upper():<10}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed >= 3:
        print("🎉 Hardware is working! You can proceed with full testing.")
    elif passed >= 2:
        print("⚠️  Basic functionality works. Check failed tests.")
    else:
        print("❌ Hardware issues detected. Check connections.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 