#!/usr/bin/env python3
"""
Test script to debug progress bar issues.
"""

import time
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ENABLE_PROGRESS_BARS, DISABLE_INDIVIDUAL_PROGRESS_BARS_IN_BATCH, PROGRESS_BAR_LOG_DELAY

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
    print("✅ tqdm is available")
except ImportError:
    TQDM_AVAILABLE = False
    print("❌ tqdm is not available")

def test_single_progress_bar():
    """Test a single progress bar."""
    print("\n=== Testing Single Progress Bar ===")
    
    if not TQDM_AVAILABLE:
        print("Skipping - tqdm not available")
        return
    
    with tqdm(
        total=5,
        desc="Test Progress",
        unit="item",
        ncols=80,
        position=0,
        leave=True,
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    ) as pbar:
        for i in range(5):
            time.sleep(0.5)
            pbar.update(1)
            pbar.set_description(f"Processing item {i+1}")

def test_multiple_progress_bars():
    """Test multiple progress bars with positioning."""
    print("\n=== Testing Multiple Progress Bars ===")
    
    if not TQDM_AVAILABLE:
        print("Skipping - tqdm not available")
        return
    
    # Overall progress bar
    with tqdm(
        total=10,
        desc="Overall Progress",
        unit="item",
        ncols=80,
        position=1,
        leave=True,
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    ) as overall_pbar:
        
        # Individual progress bar
        with tqdm(
            total=5,
            desc="Individual Progress",
            unit="item",
            ncols=80,
            position=0,
            leave=True,
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as individual_pbar:
            
            for i in range(5):
                time.sleep(0.3)
                individual_pbar.update(1)
                individual_pbar.set_description(f"Processing item {i+1}")
                
                # Update overall progress
                overall_pbar.update(2)

def test_configuration():
    """Test the current configuration."""
    print("\n=== Testing Configuration ===")
    print(f"ENABLE_PROGRESS_BARS: {ENABLE_PROGRESS_BARS}")
    print(f"DISABLE_INDIVIDUAL_PROGRESS_BARS_IN_BATCH: {DISABLE_INDIVIDUAL_PROGRESS_BARS_IN_BATCH}")
    print(f"PROGRESS_BAR_LOG_DELAY: {PROGRESS_BAR_LOG_DELAY}")
    print(f"TQDM_AVAILABLE: {TQDM_AVAILABLE}")

def test_logging_interference():
    """Test logging interference with progress bars."""
    print("\n=== Testing Logging Interference ===")
    
    if not TQDM_AVAILABLE:
        print("Skipping - tqdm not available")
        return
    
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('test')
    
    with tqdm(
        total=5,
        desc="Progress with Logging",
        unit="item",
        ncols=80,
        position=0,
        leave=True,
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    ) as pbar:
        for i in range(5):
            time.sleep(0.5)
            logger.info(f"Processing item {i+1}")
            time.sleep(PROGRESS_BAR_LOG_DELAY)  # Delay after logging
            pbar.update(1)
            pbar.set_description(f"Processing item {i+1}")

def test_logging_interference_fix():
    """Test the logging interference fix."""
    print("\n=== Testing Logging Interference Fix ===")
    
    if not TQDM_AVAILABLE:
        print("Skipping - tqdm not available")
        return
    
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('test')
    
    def update_progress_bar_safely(progress_bar, value=1, description=None):
        """Update progress bar safely without logging interference."""
        if progress_bar:
            # Temporarily disable logging during progress bar update
            original_handlers = logging.getLogger().handlers[:]
            logging.getLogger().handlers.clear()
            
            try:
                progress_bar.update(value)
                if description:
                    progress_bar.set_description(description)
            finally:
                # Restore logging handlers
                for handler in original_handlers:
                    logging.getLogger().addHandler(handler)
    
    with tqdm(
        total=5,
        desc="Progress with Logging Fix",
        unit="item",
        ncols=80,
        position=0,
        leave=True,
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    ) as pbar:
        for i in range(5):
            time.sleep(0.5)
            logger.info(f"Processing item {i+1}")
            update_progress_bar_safely(pbar, 1, f"Processing item {i+1}")

if __name__ == "__main__":
    test_configuration()
    test_single_progress_bar()
    test_multiple_progress_bars()
    test_logging_interference()
    test_logging_interference_fix()
    
    print("\n=== Summary ===")
    print("If progress bars are not working, check:")
    print("1. tqdm is installed: pip install tqdm")
    print("2. Terminal supports progress bars")
    print("3. No other output is interfering")
    print("4. Configuration values are correct")
    print("5. Logging interference has been fixed") 