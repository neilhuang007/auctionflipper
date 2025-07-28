#!/usr/bin/env python3
"""
Startup Script for Optimized AuctionFlipper

This script handles the startup of both the evaluation service and the main application.
"""

import subprocess
import sys
import time
import requests
import argparse
import os
import signal
from concurrent.futures import ThreadPoolExecutor

def check_service_health(url="http://localhost:3000/health", timeout=5):
    """Check if the evaluation service is running."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_evaluation_service():
    """Start the Node.js evaluation service."""
    print("🚀 Starting evaluation service...")
    
    try:
        # Start the Node.js service
        process = subprocess.Popen(
            ['node', 'EvaluatorService.js'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for service to start
        print("⏳ Waiting for evaluation service to start...")
        max_attempts = 30
        for attempt in range(max_attempts):
            if check_service_health():
                print("✅ Evaluation service is ready!")
                return process
            time.sleep(1)
            print(f"   Attempt {attempt + 1}/{max_attempts}...")
        
        print("❌ Evaluation service failed to start within 30 seconds")
        process.terminate()
        return None
        
    except FileNotFoundError:
        print("❌ Node.js not found. Please ensure Node.js is installed and in PATH.")
        return None
    except Exception as e:
        print(f"❌ Error starting evaluation service: {e}")
        return None

def start_python_application(optimized=True):
    """Start the Python application."""
    script = "AuctionFlipperCoreOptimized.py" if optimized else "AuctionFlipperCore.py"
    
    print(f"🐍 Starting {'optimized' if optimized else 'original'} Python application...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return process
    except Exception as e:
        print(f"❌ Error starting Python application: {e}")
        return None

def monitor_process(process, name):
    """Monitor a process and print its output."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{name}] {line.rstrip()}")
        process.wait()
    except Exception as e:
        print(f"❌ Error monitoring {name}: {e}")

def run_performance_comparison():
    """Run a performance comparison between original and optimized versions."""
    print("🏁 Running Performance Comparison")
    print("=" * 50)
    
    # Check if evaluation service is running
    if not check_service_health():
        print("❌ Evaluation service not running. Starting it first...")
        service_process = start_evaluation_service()
        if not service_process:
            return
    else:
        print("✅ Evaluation service is already running")
        service_process = None
    
    comparison_results = {}
    
    # Test original version (if available)
    if os.path.exists("AuctionFlipperCore.py"):
        print("\n🔵 Testing original version...")
        start_time = time.time()
        
        try:
            # Run original for a short time (30 seconds)
            original_process = start_python_application(optimized=False)
            if original_process:
                time.sleep(30)  # Let it run for 30 seconds
                original_process.terminate()
                original_process.wait()
                comparison_results['original'] = time.time() - start_time
                print(f"✅ Original version test completed")
        except Exception as e:
            print(f"❌ Error testing original version: {e}")
    
    # Test optimized version
    print("\n🟢 Testing optimized version...")
    start_time = time.time()
    
    try:
        optimized_process = start_python_application(optimized=True)
        if optimized_process:
            time.sleep(30)  # Let it run for 30 seconds
            optimized_process.terminate()
            optimized_process.wait()
            comparison_results['optimized'] = time.time() - start_time
            print(f"✅ Optimized version test completed")
    except Exception as e:
        print(f"❌ Error testing optimized version: {e}")
    
    # Clean up service if we started it
    if service_process:
        service_process.terminate()
        service_process.wait()
    
    # Print comparison results
    print(f"\n📊 Performance Comparison Results")
    print("=" * 40)
    
    if 'original' in comparison_results and 'optimized' in comparison_results:
        improvement = ((comparison_results['original'] - comparison_results['optimized']) / 
                      comparison_results['original']) * 100
        print(f"Original version: {comparison_results['original']:.2f}s")
        print(f"Optimized version: {comparison_results['optimized']:.2f}s")
        print(f"Performance improvement: {improvement:.1f}%")
    else:
        print("❌ Unable to complete comparison - missing versions")

def setup_database_indexes():
    """Setup database indexes if not already present."""
    try:
        print("🔧 Setting up database indexes...")
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from Handlers.DataBaseHandler import setup_database_indexes as setup_indexes
        setup_indexes()
        print("✅ Database indexes configured")
        return True
    except Exception as e:
        print(f"❌ Error setting up database indexes: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='AuctionFlipper Startup Manager')
    parser.add_argument('--mode', choices=['optimized', 'original', 'service-only', 'compare'], 
                       default='optimized', help='Startup mode (default: optimized)')
    parser.add_argument('--no-service', action='store_true', 
                       help='Skip starting evaluation service (assume already running)')
    parser.add_argument('--skip-db-setup', action='store_true',
                       help='Skip database index setup')
    
    args = parser.parse_args()
    
    # Setup database indexes unless skipped
    if not args.skip_db_setup:
        if not setup_database_indexes():
            print("⚠️  Database setup failed, continuing anyway...")
    else:
        print("⏭️  Skipping database setup")
    
    if args.mode == 'compare':
        run_performance_comparison()
        return
    
    processes = []
    
    try:
        # Start evaluation service if needed
        service_process = None
        if not args.no_service and args.mode != 'original':
            if not check_service_health():
                service_process = start_evaluation_service()
                if not service_process:
                    print("❌ Failed to start evaluation service")
                    return
                processes.append(('EvaluationService', service_process))
            else:
                print("✅ Evaluation service already running")
        
        # Start Python application if not service-only mode
        if args.mode != 'service-only':
            python_process = start_python_application(optimized=(args.mode == 'optimized'))
            if python_process:
                processes.append(('PythonApp', python_process))
            else:
                print("❌ Failed to start Python application")
                return
        
        if not processes:
            print("❌ No processes started")
            return
        
        print(f"\n✅ All services started successfully!")
        print("Press Ctrl+C to stop all services gracefully")
        
        # Monitor all processes
        with ThreadPoolExecutor(max_workers=len(processes)) as executor:
            futures = [
                executor.submit(monitor_process, process, name) 
                for name, process in processes
            ]
            
            # Wait for any process to finish or for interruption
            try:
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                print("\n🛑 Interrupt received, stopping services...")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupt received, stopping services...")
    
    finally:
        # Clean up all processes
        print("🧹 Cleaning up processes...")
        for name, process in processes:
            try:
                if process.poll() is None:  # Process is still running
                    print(f"  Stopping {name}...")
                    process.terminate()
                    process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"  Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"  Error stopping {name}: {e}")
        
        print("✅ Cleanup completed")

if __name__ == "__main__":
    main()