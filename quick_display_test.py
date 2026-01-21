#!/usr/bin/env python3
"""
Quick Display Test
Simple test to verify pygame display works
"""

import os
import pygame
import time

def main():
    print("Quick Display Test")
    
    # Set environment
    os.environ['DISPLAY'] = ':0'
    os.environ['XAUTHORITY'] = '/home/pi/.Xauthority'
    
    print(f"DISPLAY: {os.environ.get('DISPLAY')}")
    print(f"XAUTHORITY: {os.environ.get('XAUTHORITY')}")
    
    try:
        pygame.init()
        print("✓ Pygame initialized")
        
        # Create a simple window
        screen = pygame.display.set_mode((800, 600))
        print("✓ Display surface created")
        
        # Fill with blue
        screen.fill((0, 0, 255))
        pygame.display.flip()
        print("✓ Blue screen displayed")
        
        # Wait 3 seconds
        print("Displaying blue screen for 3 seconds...")
        time.sleep(3)
        
        # Fill with green
        screen.fill((0, 255, 0))
        pygame.display.flip()
        print("✓ Green screen displayed")
        
        # Wait 3 seconds
        print("Displaying green screen for 3 seconds...")
        time.sleep(3)
        
        # Fill with red
        screen.fill((255, 0, 0))
        pygame.display.flip()
        print("✓ Red screen displayed")
        
        # Wait 3 seconds
        print("Displaying red screen for 3 seconds...")
        time.sleep(3)
        
        pygame.quit()
        print("✓ Test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
