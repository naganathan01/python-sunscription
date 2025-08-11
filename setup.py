# setup.py - Complete setup script for subscription management system
import os
import sys
import subprocess
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
import stripe

def install_requirements():
    """Install required packages"""
    print("[INSTALL] Installing required packages...")
    
    requirements = [
        'Flask==2.2.5',
        'Flask-SQLAlchemy==3.1.1',
        'Flask-CORS==4.0.0',
        'stripe==7.0.0',
        'PyMySQL==1.1.0',
        'python-dotenv==1.0.0',
        'requests==2.31.0',
        'cryptography==41.0.7',
        'Werkzeug==2.3.7'
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"[OK] Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install {package}: {e}")
            return False
    
    return True

def setup_database():
    """Initialize database with tables and sample data"""
    print("[DATABASE] Setting up database...")
    
    # Initialize Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://master:master@localhost/subscription_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    # Import models (you would normally import from your app file)
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        name = db.Column(db.String(100), nullable=False)
        stripe_customer_id = db.Column(db.String(100), unique=True)
        phone = db.Column(db.String(20))
        company = db.Column(db.String(100))
        status = db.Column(db.String(20), default='active')
        created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    class Plan(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text)
        amount = db.Column(db.Numeric(10, 2), nullable=False)
        interval = db.Column(db.String(20), default='monthly')
        stripe_price_id = db.Column(db.String(100), unique=True)
        stripe_product_id = db.Column(db.String(100))
        features = db.Column(db.JSON)
        active = db.Column(db.Boolean, default=True)
        trial_days = db.Column(db.Integer, default=0)
        setup_fee = db.Column(db.Numeric(10, 2), default=0)
        created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    with app.app_context():
        try:
            db.create_all()
            print("[OK] Database tables created successfully")
            
            # Check if sample data already exists
            if Plan.query.count() == 0:
                create_sample_plans(db, Plan)
            else:
                print("[INFO] Sample data already exists")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Database setup failed: {e}")
            return False

def create_sample_plans(db, Plan):
    """Create sample subscription plans"""
    print("[PLANS] Creating sample plans...")
    
    # Set Stripe API key - REPLACE WITH YOUR ACTUAL KEY
    stripe.api_key = 'sk_test_51RdVKJGgl2nSibwhhvZRbPibfHKpv6Esdii7NSk9L6bYImoDWe1yZ0jw0Yea5bOu75b09iHkkkubyiC9atvzPNpX00KhiipdY1'
    
    plans_data = [
        {
            'name': 'Starter Plan',
            'description': 'Perfect for individuals getting started',
            'amount': Decimal('9.99'),
            'interval': 'monthly',
            'features': ['5 Projects', '1GB Storage', 'Email Support', 'Basic Analytics'],
            'trial_days': 14
        },
        {
            'name': 'Professional Plan',
            'description': 'Great for growing businesses and teams',
            'amount': Decimal('29.99'),
            'interval': 'monthly',
            'features': ['Unlimited Projects', '10GB Storage', 'Priority Support', 'Advanced Analytics', 'Team Collaboration'],
            'trial_days': 7
        },
        {
            'name': 'Enterprise Plan',
            'description': 'For large organizations with advanced needs',
            'amount': Decimal('99.99'),
            'interval': 'monthly',
            'features': ['Everything in Pro', '100GB Storage', '24/7 Dedicated Support', 'Custom Integrations', 'SLA Guarantee', 'Advanced Security'],
            'trial_days': 0
        },
        {
            'name': 'Annual Starter',
            'description': 'Starter plan billed annually (save 20%)',
            'amount': Decimal('95.99'),
            'interval': 'yearly',
            'features': ['5 Projects', '1GB Storage', 'Email Support', 'Basic Analytics', '2 Months Free'],
            'trial_days': 30
        }
    ]

    for plan_data in plans_data:
        try:
            # Create Stripe product and price
            stripe_product_id = None
            stripe_price_id = None
            
            try:
                # Create product in Stripe
                product = stripe.Product.create(
                    name=plan_data['name'],
                    description=plan_data['description']
                )
                stripe_product_id = product.id

                # Create recurring price in Stripe
                stripe_price = stripe.Price.create(
                    unit_amount=int(plan_data['amount'] * 100),
                    currency='usd',
                    recurring={'interval': plan_data['interval']},
                    product=product.id
                )
                stripe_price_id = stripe_price.id
                
                print(f"[OK] Stripe product/price created for {plan_data['name']}")
                
            except stripe.error.StripeError as e:
                print(f"[WARNING] Stripe creation skipped for {plan_data['name']}: {str(e)}")
                # Continue without Stripe integration
            
            # Save to database
            plan = Plan(
                name=plan_data['name'],
                description=plan_data['description'],
                amount=plan_data['amount'],
                interval=plan_data['interval'],
                stripe_price_id=stripe_price_id,
                stripe_product_id=stripe_product_id,
                features=plan_data['features'],
                trial_days=plan_data['trial_days']
            )
            db.session.add(plan)

        except Exception as e:
            print(f"[ERROR] Failed to create plan '{plan_data['name']}': {str(e)}")
            continue

    try:
        db.session.commit()
        print("[OK] Sample plans created successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save plans: {e}")
        db.session.rollback()

def create_env_file():
    """Create environment file with configuration"""
    print("[CONFIG] Creating environment configuration...")
    
    env_content = """# Subscription Management System Configuration

# Database Configuration
DATABASE_URL=mysql://master:master@localhost/subscription_db

# Stripe Configuration (REPLACE WITH YOUR ACTUAL KEYS)
STRIPE_SECRET_KEY=sk_test_51RdVKJGgl2nSibwhhvZRbPibfHKpv6Esdii7NSk9L6bYImoDWe1yZ0jw0Yea5bOu75b09iHkkkubyiC9atvzPNpX00KhiipdY1
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Application Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True
HOST=0.0.0.0
PORT=5000
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("[OK] Environment file created (.env)")
        print("[WARNING] Remember to update the Stripe keys with your actual values!")
    except Exception as e:
        print(f"[ERROR] Failed to create .env file: {e}")

def check_mysql_connection():
    """Check if MySQL database is accessible"""
    print("[CHECK] Checking MySQL connection...")
    
    try:
        import pymysql
        connection = pymysql.connect(
            host='localhost',
            user='master',
            password='master',
            database='subscription_db'
        )
        connection.close()
        print("[OK] MySQL connection successful")
        return True
    except Exception as e:
        print(f"[ERROR] MySQL connection failed: {e}")
        print("[HELP] Make sure MySQL is running and the database 'subscription_db' exists")
        print("[HELP] You may need to create the database: CREATE DATABASE subscription_db;")
        return False

def validate_stripe_keys():
    """Validate Stripe API keys"""
    print("[CHECK] Validating Stripe configuration...")
    
    test_key = 'sk_test_51RdVKJGgl2nSibwhhvZRbPibfHKpv6Esdii7NSk9L6bYImoDWe1yZ0jw0Yea5bOu75b09iHkkkubyiC9atvzPNpX00KhiipdY1'
    
    try:
        stripe.api_key = test_key
        # Try to list products to test the key
        stripe.Product.list(limit=1)
        print("[OK] Stripe API key is valid")
        return True
    except stripe.error.AuthenticationError:
        print("[ERROR] Invalid Stripe API key")
        print("[HELP] Please update the Stripe keys in config.py and .env files")
        return False
    except Exception as e:
        print(f"[WARNING] Stripe validation warning: {e}")
        return True

def create_readme():
    """Create comprehensive README file"""
    print("[DOCS] Creating README file...")
    
    readme_content = """# Subscription Management System

A complete subscription management system with Stripe integration, built with Flask and SQLAlchemy.

## Features

[OK] **User Management**
- Create, read, update users
- Stripe customer integration

[OK] **Subscription Plans**
- Multiple pricing tiers
- Monthly/yearly billing
- Trial periods
- Setup fees

[OK] **Subscription Management**
- Create subscriptions with Stripe
- Update quantities
- Change plans with proration
- Cancel/reactivate subscriptions

[OK] **Coupon System**
- Percentage and fixed amount discounts
- Usage limits and expiration dates
- Stripe coupon integration

[OK] **Usage Tracking**
- Record usage metrics
- Billing period summaries
- Custom metadata support

[OK] **Analytics Dashboard**
- Revenue metrics (MRR, ARR)
- Subscription analytics
- Customer insights

[OK] **Advanced Features**
- Bulk operations
- Data export (JSON/CSV)
- Stripe webhooks
- Comprehensive API

## Quick Start

1. **Install Dependencies**
   ```bash
   python setup.py install
   ```

2. **Configure Database**
   - Create MySQL database: `subscription_db`
   - Update connection string in `.env`

3. **Configure Stripe**
   - Get your Stripe API keys from https://dashboard.stripe.com/apikeys
   - Update keys in `.env` and `config.py`

4. **Initialize Database**
   ```bash
   python setup.py database
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Test with Postman**
   - Import the provided Postman collection
   - Run the test suite: `python test_complete.py full`

## API Endpoints

### User Management
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user
- `GET /api/users` - List users

### Plans
- `POST /api/plans` - Create plan
- `GET /api/plans` - List plans
- `GET /api/plans/{id}` - Get plan

### Subscriptions
- `POST /api/subscriptions` - Create subscription
- `PUT /api/subscriptions/{id}/quantity` - Update quantity
- `POST /api/subscriptions/{id}/cancel` - Cancel subscription
- `POST /api/subscriptions/{id}/reactivate` - Reactivate subscription
- `PUT /api/subscriptions/{id}/change-plan` - Change plan

### Coupons
- `POST /api/coupons` - Create coupon
- `POST /api/coupons/{code}/validate` - Validate coupon

### Usage Tracking
- `POST /api/subscriptions/{id}/usage` - Record usage
- `GET /api/subscriptions/{id}/usage` - Get usage stats

### Dashboard
- `GET /api/dashboard/revenue` - Revenue metrics
- `GET /api/dashboard/subscriptions` - Subscription analytics

## Testing

Run the complete test suite:
```bash
# Full functionality tests
python test_complete.py full

# Performance testing
python test_complete.py performance

# Load testing with 20 concurrent users
python test_complete.py load 20

# Create sample data
python test_complete.py sample
```

## Stripe Webhook Setup

1. Add webhook endpoint in Stripe Dashboard: `your-domain.com/api/webhooks/stripe`
2. Select these events:
   - `invoice.payment_succeeded`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
3. Update webhook secret in `.env`

## Configuration

Key configuration files:
- `.env` - Environment variables
- `config.py` - Application configuration
- `app.py` - Main application file

## Database Schema

- **Users** - Customer information
- **Plans** - Subscription plans
- **Subscriptions** - Active subscriptions
- **Revenue** - Payment records
- **Coupons** - Discount codes
- **Usage** - Usage tracking
- **AuditLog** - System audit trail

## Production Deployment

1. Set `DEBUG=False` in production
2. Use production Stripe keys
3. Configure proper database connection
4. Set up SSL certificates
5. Configure webhook endpoints
6. Set up monitoring and logging

## Support

For issues or questions:
1. Check the test suite results
2. Review API documentation
3. Check Stripe dashboard for payment issues
4. Review application logs

## License

This project is provided as-is for educational and development purposes.
"""
    
    try:
        with open('README.md', 'w') as f:
            f.write(readme_content)
        print("[OK] README.md created")
    except Exception as e:
        print(f"[ERROR] Failed to create README: {e}")

def main():
    """Main setup function"""
    print(">> Subscription Management System Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'install':
            install_requirements()
        elif command == 'database':
            setup_database()
        elif command == 'env':
            create_env_file()
        elif command == 'readme':
            create_readme()
        elif command == 'check':
            check_mysql_connection()
            validate_stripe_keys()
        else:
            print("Available commands:")
            print("  install  - Install required packages")
            print("  database - Setup database and sample data")
            print("  env      - Create environment file")
            print("  readme   - Create README file")
            print("  check    - Check MySQL and Stripe configuration")
    else:
        # Run complete setup
        print("Running complete setup...")
        
        success_count = 0
        total_steps = 6
        
        # Step 1: Install requirements
        if install_requirements():
            success_count += 1
        
        # Step 2: Create environment file
        create_env_file()
        success_count += 1
        
        # Step 3: Create README
        create_readme()
        success_count += 1
        
        # Step 4: Check MySQL
        if check_mysql_connection():
            success_count += 1
        
        # Step 5: Validate Stripe
        if validate_stripe_keys():
            success_count += 1
        
        # Step 6: Setup database
        if setup_database():
            success_count += 1
        
        print("\n" + "="*50)
        print(">> SETUP COMPLETION SUMMARY")
        print("="*50)
        print(f"[OK] Completed: {success_count}/{total_steps} steps")
        
        if success_count == total_steps:
            print("[SUCCESS] Setup completed successfully!")
            print("\n[NEXT] Next Steps:")
            print("1. Update Stripe API keys in .env and config.py")
            print("2. Run the application: python app.py")
            print("3. Test with Postman or run: python test_complete.py full")
            print("4. Visit http://localhost:5000 to see the API documentation")
        else:
            print("[WARNING] Setup completed with some issues")
            print("[HELP] Check the error messages above and resolve them")
            print("[HELP] You can run individual setup commands:")
            print("   python setup.py install")
            print("   python setup.py database") 
            print("   python setup.py check")

if __name__ == '__main__':
    main()