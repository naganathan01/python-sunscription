# app.py - Complete working subscription management system
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import stripe
import os
from decimal import Decimal
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://master:master@localhost/subscription_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Stripe configuration - REPLACE WITH YOUR ACTUAL KEYS
stripe.api_key = 'sk_test_51RdVKJGgl2nSibwhhvZRbPibfHKpv6Esdii7NSk9L6bYImoDWe1yZ0jw0Yea5bOu75b09iHkkkubyiC9atvzPNpX00KhiipdY1'

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    stripe_customer_id = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Fixed: renamed from price
    interval = db.Column(db.String(20), default='monthly')
    stripe_price_id = db.Column(db.String(100), unique=True)
    stripe_product_id = db.Column(db.String(100))
    features = db.Column(db.JSON)
    active = db.Column(db.Boolean, default=True)
    trial_days = db.Column(db.Integer, default=0)
    setup_fee = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.relationship('Subscription', backref='plan', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(50), default='active')
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    quantity = db.Column(db.Integer, default=1)
    trial_end = db.Column(db.DateTime)
    canceled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Revenue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='usd')
    stripe_invoice_id = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='paid')
    description = db.Column(db.String(255))

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed_amount
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    stripe_coupon_id = db.Column(db.String(100))
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer)
    current_uses = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    usage_data = db.Column(db.String(255))

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    metadata = db.Column(db.JSON)  # Fixed: was usage_data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

# Helper Functions
def create_stripe_customer(email, name):
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")

def log_audit(user_id, action, description, metadata=None):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        description=description,
        metadata=metadata,
        ip_address=request.remote_addr
    )
    db.session.add(audit)

# Health Check
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# User Management Routes
@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        email = data.get('email')
        name = data.get('name')
        phone = data.get('phone')
        company = data.get('company')

        if not email or not name:
            return jsonify({'error': 'Email and name are required'}), 400

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409

        # Create Stripe customer
        stripe_customer_id = None
        try:
            stripe_customer_id = create_stripe_customer(email, name)
        except Exception as e:
            print(f"Stripe customer creation failed: {e}")
            # Continue without Stripe customer for testing

        # Create user
        user = User(
            email=email,
            name=name,
            phone=phone,
            company=company,
            stripe_customer_id=stripe_customer_id
        )
        db.session.add(user)
        db.session.commit()

        log_audit(user.id, 'USER_CREATED', f'User {email} created')
        db.session.commit()

        return jsonify({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'company': user.company,
            'stripe_customer_id': user.stripe_customer_id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get subscription summary
    active_subs = Subscription.query.filter_by(user_id=user_id, status='active').count()
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'company': user.company,
        'phone': user.phone,
        'status': user.status,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'active_subscriptions': active_subs,
        'stripe_customer_id': user.stripe_customer_id
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    email = request.args.get('email')
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify([{
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'stripe_customer_id': user.stripe_customer_id
            }])
        return jsonify([])
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'stripe_customer_id': user.stripe_customer_id
    } for user in users])

# Plan Management Routes
@app.route('/api/plans', methods=['POST'])
def create_plan():
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        amount = Decimal(str(data.get('amount')))  # Fixed: changed from price
        interval = data.get('interval', 'monthly')
        features = data.get('features', [])
        trial_days = data.get('trial_days', 0)
        setup_fee = data.get('setup_fee', 0)

        if not name or not amount:
            return jsonify({'error': 'Name and amount are required'}), 400

        # Create Stripe product and price
        stripe_product_id = None
        stripe_price_id = None
        
        try:
            # Create Stripe product
            product = stripe.Product.create(
                name=name,
                description=description
            )
            stripe_product_id = product.id

            # Create Stripe price
            stripe_price = stripe.Price.create(
                unit_amount=int(amount * 100),  # Convert to cents
                currency='usd',
                recurring={'interval': interval},
                product=product.id
            )
            stripe_price_id = stripe_price.id
        except Exception as e:
            print(f"Stripe product/price creation failed: {e}")
            # Continue without Stripe for testing

        # Create plan in database
        plan = Plan(
            name=name,
            description=description,
            amount=amount,  # Fixed: changed from price
            interval=interval,
            stripe_price_id=stripe_price_id,
            stripe_product_id=stripe_product_id,
            features=features,
            trial_days=trial_days,
            setup_fee=setup_fee
        )
        db.session.add(plan)
        db.session.commit()

        log_audit(None, 'PLAN_CREATED', f'Plan {name} created with amount ${amount}')
        db.session.commit()

        return jsonify({
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'amount': float(plan.amount),
            'interval': plan.interval,
            'features': plan.features,
            'trial_days': plan.trial_days,
            'setup_fee': float(plan.setup_fee),
            'stripe_price_id': plan.stripe_price_id,
            'stripe_product_id': plan.stripe_product_id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/plans', methods=['GET'])
def get_plans():
    plans = Plan.query.filter_by(active=True).all()
    return jsonify([{
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'amount': float(plan.amount),
        'interval': plan.interval,
        'features': plan.features,
        'trial_days': plan.trial_days,
        'setup_fee': float(plan.setup_fee),
        'stripe_price_id': plan.stripe_price_id
    } for plan in plans])

@app.route('/api/plans/<int:plan_id>', methods=['GET'])
def get_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)
    return jsonify({
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'amount': float(plan.amount),
        'interval': plan.interval,
        'features': plan.features,
        'trial_days': plan.trial_days,
        'setup_fee': float(plan.setup_fee),
        'stripe_price_id': plan.stripe_price_id
    })

# Coupon Management Routes
@app.route('/api/coupons', methods=['POST'])
def create_coupon():
    try:
        data = request.json
        code = data.get('code')
        discount_type = data.get('discount_type')
        discount_value = Decimal(str(data.get('discount_value')))
        valid_until = data.get('valid_until')
        max_uses = data.get('max_uses')
        
        if not all([code, discount_type, discount_value]):
            return jsonify({'error': 'Code, discount_type, and discount_value are required'}), 400
        
        # Create Stripe coupon
        stripe_coupon_id = None
        try:
            stripe_coupon_data = {
                'id': code,
                'name': code,
            }
            
            if discount_type == 'percentage':
                stripe_coupon_data['percent_off'] = float(discount_value)
            else:
                stripe_coupon_data['amount_off'] = int(discount_value * 100)
                stripe_coupon_data['currency'] = 'usd'
            
            if valid_until:
                stripe_coupon_data['redeem_by'] = int(datetime.fromisoformat(valid_until).timestamp())
            
            if max_uses:
                stripe_coupon_data['max_redemptions'] = max_uses
            
            stripe_coupon = stripe.Coupon.create(**stripe_coupon_data)
            stripe_coupon_id = stripe_coupon.id
        except Exception as e:
            print(f"Stripe coupon creation failed: {e}")
        
        # Create coupon in database
        coupon = Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            stripe_coupon_id=stripe_coupon_id,
            valid_until=datetime.fromisoformat(valid_until) if valid_until else None,
            max_uses=max_uses
        )
        db.session.add(coupon)
        db.session.commit()
        
        log_audit(None, 'COUPON_CREATED', f'Coupon {code} created')
        db.session.commit()
        
        return jsonify({
            'id': coupon.id,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'stripe_coupon_id': coupon.stripe_coupon_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/coupons/<code>/validate', methods=['POST'])
def validate_coupon(code):
    coupon = Coupon.query.filter_by(code=code, active=True).first()
    
    if not coupon:
        return jsonify({'valid': False, 'error': 'Coupon not found'}), 404
    
    # Check validity
    now = datetime.utcnow()
    if coupon.valid_until and now > coupon.valid_until:
        return jsonify({'valid': False, 'error': 'Coupon expired'}), 400
    
    if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
        return jsonify({'valid': False, 'error': 'Coupon usage limit reached'}), 400
    
    return jsonify({
        'valid': True,
        'discount_type': coupon.discount_type,
        'discount_value': float(coupon.discount_value),
        'stripe_coupon_id': coupon.stripe_coupon_id
    })

# Subscription Management Routes
@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    try:
        data = request.json
        user_id = data.get('user_id')
        plan_id = data.get('plan_id')
        quantity = data.get('quantity', 1)
        coupon_code = data.get('coupon_code')

        if not user_id or not plan_id:
            return jsonify({'error': 'User ID and Plan ID are required'}), 400

        user = User.query.get(user_id)
        plan = Plan.query.get(plan_id)

        if not user or not plan:
            return jsonify({'error': 'User or Plan not found'}), 404

        # Create Stripe subscription
        stripe_subscription_id = None
        try:
            if user.stripe_customer_id and plan.stripe_price_id:
                subscription_data = {
                    'customer': user.stripe_customer_id,
                    'items': [{
                        'price': plan.stripe_price_id,
                        'quantity': quantity,
                    }],
                    'expand': ['latest_invoice.payment_intent'],
                }
                
                # Add trial period if available
                if plan.trial_days > 0:
                    subscription_data['trial_period_days'] = plan.trial_days
                
                # Add coupon if provided
                if coupon_code:
                    coupon = Coupon.query.filter_by(code=coupon_code, active=True).first()
                    if coupon and coupon.stripe_coupon_id:
                        subscription_data['coupon'] = coupon.stripe_coupon_id
                        # Update coupon usage
                        coupon.current_uses += 1
                
                stripe_subscription = stripe.Subscription.create(**subscription_data)
                stripe_subscription_id = stripe_subscription.id
                
                # Get the client secret for frontend payment confirmation
                client_secret = None
                if stripe_subscription.latest_invoice.payment_intent:
                    client_secret = stripe_subscription.latest_invoice.payment_intent.client_secret
                
        except stripe.error.StripeError as e:
            return jsonify({'error': f'Stripe error: {str(e)}'}), 400

        # Create subscription in database
        trial_end = None
        if plan.trial_days > 0:
            trial_end = datetime.utcnow() + timedelta(days=plan.trial_days)

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_subscription_id=stripe_subscription_id,
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            quantity=quantity,
            trial_end=trial_end
        )
        db.session.add(subscription)
        db.session.commit()

        log_audit(user_id, 'SUBSCRIPTION_CREATED', f'Subscription created for plan {plan.name}', {
            'subscription_id': subscription.id,
            'plan_id': plan_id,
            'quantity': quantity,
            'coupon_code': coupon_code
        })
        db.session.commit()

        return jsonify({
            'subscription_id': subscription.id,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'status': subscription.status,
            'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
            'client_secret': client_secret or 'no_payment_required'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscriptions/<int:subscription_id>/quantity', methods=['PUT'])
def update_subscription_quantity(subscription_id):
    try:
        data = request.json
        quantity = data.get('quantity')

        if not quantity or quantity < 1:
            return jsonify({'error': 'Valid quantity is required'}), 400

        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404

        # Update Stripe subscription
        try:
            if subscription.stripe_subscription_id:
                stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_subscription['items']['data'][0].id,
                        'quantity': quantity,
                    }]
                )
        except stripe.error.StripeError as e:
            return jsonify({'error': f'Stripe error: {str(e)}'}), 400

        # Update local subscription
        old_quantity = subscription.quantity
        subscription.quantity = quantity
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        log_audit(subscription.user_id, 'SUBSCRIPTION_QUANTITY_UPDATED', 
                 f'Quantity changed from {old_quantity} to {quantity}', {
            'subscription_id': subscription_id,
            'old_quantity': old_quantity,
            'new_quantity': quantity
        })
        db.session.commit()

        return jsonify({
            'subscription_id': subscription_id,
            'quantity': quantity,
            'message': 'Quantity updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscriptions/<int:subscription_id>/cancel', methods=['POST'])
def cancel_subscription(subscription_id):
    try:
        data = request.json
        immediate = data.get('immediate', False)

        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404

        # Cancel in Stripe
        try:
            if subscription.stripe_subscription_id:
                if immediate:
                    stripe.Subscription.cancel(subscription.stripe_subscription_id)
                else:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
        except stripe.error.StripeError as e:
            return jsonify({'error': f'Stripe error: {str(e)}'}), 400

        # Update local subscription
        if immediate:
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.utcnow()
            subscription.cancel_at_period_end = False
        else:
            subscription.cancel_at_period_end = True

        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        log_audit(subscription.user_id, 'SUBSCRIPTION_CANCELED', 
                 f'Subscription canceled (immediate: {immediate})', {
            'subscription_id': subscription_id,
            'immediate': immediate
        })
        db.session.commit()

        return jsonify({
            'subscription_id': subscription_id,
            'status': subscription.status,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'message': 'Subscription canceled successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscriptions/<int:subscription_id>/reactivate', methods=['POST'])
def reactivate_subscription(subscription_id):
    try:
        subscription = Subscription.query.get(subscription_id)
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404

        # Reactivate in Stripe
        try:
            if subscription.stripe_subscription_id:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=False
                )
        except stripe.error.StripeError as e:
            return jsonify({'error': f'Stripe error: {str(e)}'}), 400

        # Reactivate subscription
        subscription.status = 'active'
        subscription.cancel_at_period_end = False
        subscription.canceled_at = None
        subscription.updated_at = datetime.utcnow()
        db.session.commit()

        log_audit(subscription.user_id, 'SUBSCRIPTION_REACTIVATED', 
                 'Subscription reactivated', {
            'subscription_id': subscription_id
        })
        db.session.commit()

        return jsonify({
            'subscription_id': subscription_id,
            'status': subscription.status,
            'message': 'Subscription reactivated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscriptions/<int:subscription_id>/change-plan', methods=['PUT'])
def change_subscription_plan(subscription_id):
    try:
        data = request.json
        new_plan_id = data.get('plan_id')
        prorate = data.get('prorate', True)
        
        if not new_plan_id:
            return jsonify({'error': 'New plan ID is required'}), 400
        
        subscription = Subscription.query.get(subscription_id)
        new_plan = Plan.query.get(new_plan_id)
        
        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404
        if not new_plan:
            return jsonify({'error': 'New plan not found'}), 404
        
        if subscription.plan_id == new_plan_id:
            return jsonify({'error': 'User is already on this plan'}), 400
        
        # Update Stripe subscription
        try:
            if subscription.stripe_subscription_id and new_plan.stripe_price_id:
                stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_subscription['items']['data'][0].id,
                        'price': new_plan.stripe_price_id,
                    }],
                    proration_behavior='create_prorations' if prorate else 'none'
                )
        except stripe.error.StripeError as e:
            return jsonify({'error': f'Stripe error: {str(e)}'}), 400
        
        # Update local subscription
        old_plan = Plan.query.get(subscription.plan_id)
        subscription.plan_id = new_plan_id
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        log_audit(subscription.user_id, 'PLAN_CHANGED', 
                 f'Plan changed from {old_plan.name} to {new_plan.name}', {
            'old_plan_id': old_plan.id,
            'new_plan_id': new_plan_id,
            'prorate': prorate
        })
        db.session.commit()
        
        return jsonify({
            'subscription_id': subscription_id,
            'new_plan': {
                'id': new_plan.id,
                'name': new_plan.name,
                'amount': float(new_plan.amount)
            },
            'message': 'Plan changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/subscriptions', methods=['GET'])
def get_user_subscriptions(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    
    result = []
    for sub in subscriptions:
        plan = Plan.query.get(sub.plan_id)
        result.append({
            'id': sub.id,
            'plan': {
                'id': plan.id,
                'name': plan.name,
                'amount': float(plan.amount),
                'interval': plan.interval
            },
            'status': sub.status,
            'quantity': sub.quantity,
            'current_period_start': sub.current_period_start.isoformat() if sub.current_period_start else None,
            'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
            'cancel_at_period_end': sub.cancel_at_period_end,
            'trial_end': sub.trial_end.isoformat() if sub.trial_end else None,
            'stripe_subscription_id': sub.stripe_subscription_id,
            'created_at': sub.created_at.isoformat()
        })