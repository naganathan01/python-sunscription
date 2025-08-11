#!/usr/bin/env python3
# fix_deps.py - Fix Flask-SQLAlchemy compatibility issues

import subprocess
import sys

def uninstall_conflicting_packages():
    """Uninstall conflicting packages"""
    print("[CLEANUP] Uninstalling conflicting packages...")
    
    packages_to_uninstall = [
        'Flask',
        'Flask-SQLAlchemy', 
        'Werkzeug'
    ]
    
    for package in packages_to_uninstall:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', package, '-y'])
            print(f"[OK] Uninstalled {package}")
        except subprocess.CalledProcessError:
            print(f"[INFO] {package} was not installed or already removed")

def install_compatible_versions():
    """Install compatible versions"""
    print("[INSTALL] Installing compatible versions...")
    
    # Install specific compatible versions
    compatible_packages = [
        'Flask==2.2.5',
        'Werkzeug==2.3.7', 
        'Flask-SQLAlchemy==3.1.1',
        'Flask-CORS==4.0.0',
        'stripe==7.0.0',
        'PyMySQL==1.1.0',
        'python-dotenv==1.0.0',
        'requests==2.31.0',
        'cryptography==41.0.7'
    ]
    
    for package in compatible_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"[OK] Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install {package}: {e}")
            return False
    
    return True

def test_imports():
    """Test if imports work correctly"""
    print("[TEST] Testing imports...")
    
    try:
        from flask import Flask
        print("[OK] Flask import successful")
        
        from flask_sqlalchemy import SQLAlchemy
        print("[OK] Flask-SQLAlchemy import successful")
        
        from flask_cors import CORS
        print("[OK] Flask-CORS import successful")
        
        import stripe
        print("[OK] Stripe import successful")
        
        print("[SUCCESS] All imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

def main():
    print(">> Flask-SQLAlchemy Compatibility Fix")
    print("=" * 50)
    
    print("\n[INFO] This script will fix the Flask-SQLAlchemy compatibility issue")
    print("[INFO] by installing compatible versions of Flask packages.")
    
    response = input("\nContinue? (y/n): ").lower().strip()
    if response != 'y':
        print("[CANCELLED] Operation cancelled by user")
        return
    
    # Step 1: Uninstall conflicting packages
    uninstall_conflicting_packages()
    
    # Step 2: Install compatible versions
    if not install_compatible_versions():
        print("[ERROR] Failed to install compatible packages")
        return
    
    # Step 3: Test imports
    if test_imports():
        print("\n[SUCCESS] Dependency fix completed successfully!")
        print("[INFO] You can now run: python app.py")
    else:
        print("\n[ERROR] Some imports still failing. Manual intervention may be required.")
        print("[HELP] Try running: pip install --force-reinstall Flask==2.2.5 Flask-SQLAlchemy==3.1.1")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[CANCELLED] Operation cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        print("[HELP] Try manually running: pip install Flask==2.2.5 Flask-SQLAlchemy==3.1.1")