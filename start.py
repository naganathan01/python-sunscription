# start.py - Easy startup script for subscription management system

import os
import sys
import subprocess
import time
import webbrowser
from threading import Timer

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("[ERROR] Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_file_exists(filename):
    """Check if required file exists"""
    if os.path.exists(filename):
        print(f"[OK] Found {filename}")
        return True
    else:
        print(f"[ERROR] Missing {filename}")
        return False

def run_setup():
    """Run the setup process"""
    print("[SETUP] Running setup...")
    try:
        result = subprocess.run([sys.executable, 'setup.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Setup completed successfully")
            return True
        else:
            print(f"[ERROR] Setup failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Setup error: {e}")
        return False

def start_application():
    """Start the Flask application"""
    print("[START] Starting application...")
    try:
        # Start the Flask app
        subprocess.Popen([sys.executable, 'app.py'])
        print("[OK] Application started successfully")
        print("[INFO] Server running at: http://localhost:5000")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to start application: {e}")
        return False

def open_browser():
    """Open browser to the application"""
    def open_url():
        time.sleep(3)  # Wait for server to start
        try:
            webbrowser.open('http://localhost:5000')
            print("[INFO] Browser opened to http://localhost:5000")
        except Exception as e:
            print(f"[WARNING] Could not open browser: {e}")
    
    Timer(1.0, open_url).start()

def run_tests():
    """Run the test suite"""
    print("[TEST] Running test suite...")
    try:
        result = subprocess.run([sys.executable, 'test_complete.py', 'full'], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        return False

def show_menu():
    """Show interactive menu"""
    print("\n" + "="*60)
    print(">> SUBSCRIPTION MANAGEMENT SYSTEM")
    print("="*60)
    print("1. Quick Start (Setup + Run)")
    print("2. Setup Only")
    print("3. Run Application")
    print("4. Run Tests")
    print("5. Run Performance Tests") 
    print("6. Create Sample Data")
    print("7. Check Configuration")
    print("8. View Documentation")
    print("9. Exit")
    print("="*60)
    
    choice = input("Select an option (1-9): ").strip()
    return choice

def handle_choice(choice):
    """Handle user menu choice"""
    if choice == '1':
        # Quick Start
        print("\n[QUICK START]")
        print("-" * 30)
        
        if not check_python_version():
            return False
        
        # Check for required files
        required_files = ['app.py', 'setup.py', 'test_complete.py']
        missing_files = [f for f in required_files if not check_file_exists(f)]
        
        if missing_files:
            print(f"[ERROR] Missing required files: {', '.join(missing_files)}")
            return False
        
        # Run setup
        if not run_setup():
            return False
        
        # Start application
        if start_application():
            open_browser()
            print("\n[SUCCESS] Application is running!")
            print("[INFO] You can now:")
            print("   - Visit http://localhost:5000 for API documentation")
            print("   - Import the Postman collection for testing")
            print("   - Run tests with: python test_complete.py full")
            print("\n[WARNING] Remember to update your Stripe API keys!")
            return True
    
    elif choice == '2':
        # Setup Only
        print("\n[SETUP ONLY]")
        print("-" * 30)
        run_setup()
    
    elif choice == '3':
        # Run Application
        print("\n[RUN APPLICATION]")
        print("-" * 30)
        if start_application():
            open_browser()
            print("[OK] Application started")
            print("[INFO] Press Ctrl+C to stop the server")
    
    elif choice == '4':
        # Run Tests
        print("\n[RUN TESTS]")
        print("-" * 30)
        run_tests()
    
    elif choice == '5':
        # Performance Tests
        print("\n[PERFORMANCE TESTS]")
        print("-" * 30)
        try:
            subprocess.run([sys.executable, 'test_complete.py', 'performance'])
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    elif choice == '6':
        # Create Sample Data
        print("\n[CREATE SAMPLE DATA]")
        print("-" * 30)
        try:
            subprocess.run([sys.executable, 'test_complete.py', 'sample'])
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    elif choice == '7':
        # Check Configuration
        print("\n[CHECK CONFIGURATION]")
        print("-" * 30)
        try:
            subprocess.run([sys.executable, 'setup.py', 'check'])
        except Exception as e:
            print(f"[ERROR] Error: {e}")
    
    elif choice == '8':
        # View Documentation
        print("\n[DOCUMENTATION]")
        print("-" * 30)
        print("[API] API Endpoints:")
        print("   GET  /health - Health check")
        print("   POST /api/users - Create user")
        print("   POST /api/plans - Create plan")
        print("   POST /api/subscriptions - Create subscription")
        print("   GET  /api/dashboard/revenue - Revenue dashboard")
        print("\n[FILES] Files:")
        print("   app.py - Main application")
        print("   config.py - Configuration")
        print("   test_complete.py - Test suite")
        print("   README.md - Detailed documentation")
        print("\n[URLS] URLs:")
        print("   http://localhost:5000 - API documentation")
        print("   http://localhost:5000/health - Health check")
        print("   http://localhost:5000/api/dashboard/revenue - Revenue data")
    
    elif choice == '9':
        # Exit
        print("[EXIT] Goodbye!")
        return False
    
    else:
        print("[ERROR] Invalid choice. Please select 1-9.")
    
    return True

def main():
    """Main function"""
    print("🎯 Subscription Management System Launcher")
    
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['start', 'quick']:
            handle_choice('1')
        elif command == 'setup':
            handle_choice('2')
        elif command == 'run':
            handle_choice('3')
        elif command == 'test':
            handle_choice('4')
        elif command == 'performance':
            handle_choice('5')
        elif command == 'sample':
            handle_choice('6')
        elif command == 'check':
            handle_choice('7')
        elif command == 'help':
            print("Available commands:")
            print("  start/quick - Quick start (setup + run)")
            print("  setup - Run setup only")
            print("  run - Start application")
            print("  test - Run test suite")
            print("  performance - Run performance tests")
            print("  sample - Create sample data")
            print("  check - Check configuration")
            print("  help - Show this help")
        else:
            print(f"Unknown command: {command}")
            print("Use 'python start.py help' for available commands")
    else:
        # Interactive mode
        while True:
            choice = show_menu()
            if not handle_choice(choice):
                break
            
            if choice != '9':
                input("\nPress Enter to continue...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please check your setup and try again")