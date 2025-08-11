# Subscription Management System

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
