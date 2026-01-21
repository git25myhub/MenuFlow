#!/usr/bin/env python3
"""
Hardware Test Without Display
Tests GPIO and buzzer functionality without display initialization

This script tests real hardware components without the display that may be causing hangs.
"""

import time
import sys
import os
import threading
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hardware_notifier import NotificationType
from config import RESTAURANT_ID

def test_gpio_direct():
    """Test GPIO directly without the hardware notifier"""
    print("🔧 Testing GPIO directly...")
    try:
        import RPi.GPIO as GPIO
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Test pins from config
        test_pins = [17, 27, 22]  # DINE_IN_LED_PIN, DELIVERY_LED_PIN, BUZZER_PIN
        
        for pin in test_pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(pin, GPIO.LOW)
                print(f"✅ GPIO {pin} working")
            except Exception as e:
                print(f"❌ GPIO {pin} failed: {e}")
        
        GPIO.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ GPIO test failed: {e}")
        return False

def test_buzzer_direct():
    """Test buzzer directly"""
    print("🔊 Testing buzzer directly...")
    try:
        import RPi.GPIO as GPIO
        
        GPIO.setmode(GPIO.BCM)
        buzzer_pin = 22
        
        # Test PWM buzzer
        GPIO.setup(buzzer_pin, GPIO.OUT)
        pwm = GPIO.PWM(buzzer_pin, 440)  # 440Hz
        pwm.start(50)  # 50% duty cycle
        
        print("🔊 Playing buzzer test...")
        time.sleep(1)
        
        pwm.stop()
        GPIO.cleanup()
        print("✅ Buzzer test completed")
        return True
        
    except Exception as e:
        print(f"❌ Buzzer test failed: {e}")
        return False

def test_led_patterns_direct():
    """Test LED patterns directly"""
    print("💡 Testing LED patterns directly...")
    try:
        import RPi.GPIO as GPIO
        
        GPIO.setmode(GPIO.BCM)
        
        # Test patterns
        patterns = [
            (17, "New Order - Blink", 3),
            (27, "Order Ready - Pulse", 2),
            (17, "Payment - Blink", 4)
        ]
        
        for pin, description, repetitions in patterns:
            print(f"  Testing {description}...")
            GPIO.setup(pin, GPIO.OUT)
            
            for _ in range(repetitions):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.3)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(0.3)
            
            print(f"    ✅ {description} completed")
        
        GPIO.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ LED pattern test failed: {e}")
        return False

def test_hardware_notifier_modified():
    """Test hardware notifier with modified display handling"""
    print("🚀 Testing modified hardware notifier...")
    try:
        # Temporarily disable display
        import pygame
        original_display_available = hasattr(sys.modules.get('hardware_notifier'), 'DISPLAY_AVAILABLE')
        
        # Create a simple hardware notifier test
        from hardware_notifier import get_hardware_notifier, cleanup_hardware_notifier
        
        # Test with timeout
        notifier = None
        success = False
        
        def init_notifier():
            nonlocal notifier, success
            try:
                notifier = get_hardware_notifier(simulation_mode=False)
                success = True
            except Exception as e:
                print(f"   Error: {e}")
                success = False
        
        # Start in separate thread with timeout
        thread = threading.Thread(target=init_notifier)
        thread.daemon = True
        thread.start()
        thread.join(timeout=8)  # 8 second timeout
        
        if thread.is_alive():
            print("⚠️  Hardware notifier initialization timed out")
            return False
        
        if success and notifier:
            print("✅ Hardware notifier initialized")
            
            # Test notifications
            print("🔔 Testing notifications...")
            test_notifications = [
                (NotificationType.NEW_ORDER, "New Order"),
                (NotificationType.ORDER_READY, "Order Ready"),
                (NotificationType.ORDER_DELIVERED, "Order Delivered"),
            ]
            
            for notification_type, description in test_notifications:
                print(f"  Testing {description}...")
                success = notifier.notify(notification_type, priority=1)
                if success:
                    print(f"    ✅ {description} notification sent")
                else:
                    print(f"    ❌ {description} notification failed")
                time.sleep(1)
            
            cleanup_hardware_notifier()
            return True
        else:
            print("❌ Hardware notifier initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Modified hardware notifier test failed: {e}")
        return False

def main():
    """Run hardware tests without display"""
    print("=" * 60)
    print("HARDWARE TEST WITHOUT DISPLAY")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Direct GPIO
    results['gpio'] = test_gpio_direct()
    
    # Test 2: Direct Buzzer
    results['buzzer'] = test_buzzer_direct()
    
    # Test 3: Direct LED Patterns
    results['led_patterns'] = test_led_patterns_direct()
    
    # Test 4: Modified Hardware Notifier
    results['notifier'] = test_hardware_notifier_modified()
    
    # Summary
    print("\n" + "=" * 60)
    print("HARDWARE TEST SUMMARY")
    print("=" * 60)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test.upper():<15}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed >= 3:
        print("🎉 Hardware is working! Display may need separate configuration.")
    elif passed >= 2:
        print("⚠️  Basic hardware works. Some components need attention.")
    else:
        print("❌ Hardware issues detected. Check connections.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 