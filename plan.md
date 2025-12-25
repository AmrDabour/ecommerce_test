# Migration Plan: Factory Backend to Microservices Architecture

## Architecture Overview

Convert Factory Backend Django apps to microservices while maintaining separate databases per service:

```
Factory Backend Apps → Microservices Mapping:
- accounts → auth-service (Django, replace FastAPI)
- products → product-service (Django, replace FastAPI)  
- orders → order-service (Django, replace FastAPI)
- payments → payment-service (Django, NEW service)
- shipping → shipping-service (Django, NEW service)
- notifications → notification-service (Django, NEW service)

Keep FastAPI for:
- api-gateway (Nginx, stays as-is)
- admin-service (FastAPI, but can integrate Django admin)
```

## Phase 1: Setup Django Microservices Structure

### 1.1 Create Django Project Template

- Create `services/django_base/` with Django project template
- Setup base `settings.py` with common configuration
- Create `requirements.txt` with Django, DRF, Djoser, SimpleJWT
- Setup `manage.py` and base URL configuration
- Configure database routing for separate databases

### 1.2 Create Shared Django Utilities

- Create `services/shared/django_utils.py` for common utilities
- Setup JWT authentication middleware for inter-service communication
- Create database connection helpers
- Setup logging configuration

## Phase 2: Auth Service Migration (accounts → auth-service)

### 2.1 Replace FastAPI Auth Service with Django

- Copy `factory-ecommerce-backend/config/accounts/` to `services/auth/app/accounts/`
- Update `services/auth/app/config/settings.py`:
  - Set `AUTH_USER_MODEL = 'accounts.User'`
  - Configure database: `auth_db`
  - Setup DRF, Djoser, SimpleJWT
- Create `services/auth/app/manage.py`
- Create `services/auth/app/config/urls.py` with accounts URLs

### 2.2 Update Auth Service Dockerfile

- Change from FastAPI to Django
- Update `services/auth/Dockerfile`:
  - Use Python 3.10+
  - Install Django dependencies
  - Run migrations on startup
  - Use gunicorn/uvicorn for ASGI

### 2.3 Remove Old FastAPI Code

- Delete `services/auth/app/main.py` (FastAPI)
- Delete `services/auth/app/models.py` (SQLAlchemy)
- Delete `services/auth/app/schemas.py` (Pydantic)
- Keep only Django structure

### 2.4 Update Database Schema

- Update `database/init-microservices-complete.sql`:
  - Remove old auth_db tables
  - Add Django migrations support for auth_db
  - Ensure User model matches Factory Backend exactly

## Phase 3: Product Service Migration (products → product-service)

### 3.1 Create Django Product Service

- Copy `factory-ecommerce-backend/config/products/` to `services/product/app/products/`
- Create `services/product/app/config/settings.py`:
  - Configure `product_db` database
  - Setup DRF, filters, pagination
  - Configure media files for product images
- Create Django project structure

### 3.2 Update Product Service

- Update `services/product/app/main.py` to Django ASGI/WSGI
- Create `services/product/app/config/urls.py`
- Setup product API endpoints using DRF ViewSets
- Configure product approval workflow endpoints

### 3.3 Update Dockerfile

- Change to Django-based Dockerfile
- Setup migrations
- Configure media volume mounts

### 3.4 Database Migration

- Update `database/init-microservices-complete.sql` for product_db
- Ensure all Factory Backend product models are included

## Phase 4: Order Service Migration (orders → order-service)

### 4.1 Create Django Order Service

- Copy `factory-ecommerce-backend/config/orders/` to `services/order/app/orders/`
- Create Django project structure
- Configure `order_db` database
- Setup order API endpoints

### 4.2 Implement Order Services Layer

- Copy `factory-ecommerce-backend/config/orders/services.py` (if exists)
- Implement cart management
- Implement order creation from cart
- Implement multi-vendor order splitting

### 4.3 Update Dockerfile and Database

- Update Dockerfile for Django
- Update database schema for order_db

## Phase 5: Payment Service Creation (payments → payment-service)

### 5.1 Create New Payment Service

- Create `services/payment/` directory
- Copy `factory-ecommerce-backend/config/payments/` to `services/payment/app/payments/`
- Create Django project structure
- Configure `payment_db` database

### 5.2 Implement Stripe Integration

- Setup Stripe payment intent creation
- Implement webhook handlers
- Setup vendor payout calculations
- Implement coupon system

### 5.3 Create Dockerfile and Database

- Create `services/payment/Dockerfile`
- Update `docker-compose.yml` with payment-service
- Update database init script for payment_db

## Phase 6: Shipping Service Creation (shipping → shipping-service)

### 6.1 Create New Shipping Service

- Create `services/shipping/` directory
- Copy `factory-ecommerce-backend/config/shipping/` to `services/shipping/app/shipping/`
- Create Django project structure
- Configure `shipping_db` database

### 6.2 Implement Shipping Features

- Setup shipping methods
- Implement shipping zone calculations
- Setup shipment tracking
- Implement return requests

### 6.3 Create Dockerfile and Database

- Create `services/shipping/Dockerfile`
- Update `docker-compose.yml`
- Update database init script

## Phase 7: Notification Service Creation (notifications → notification-service)

### 7.1 Create Notification Service

- Create `services/notification/` directory
- Copy `factory-ecommerce-backend/config/notifications/` to `services/notification/app/notifications/`
- Create Django project structure
- Configure `notification_db` database

### 7.2 Implement Notification Features

- Setup in-app notifications
- Implement email notification tracking
- Setup notification preferences
- Configure email templates

### 7.3 Create Dockerfile and Database

- Create `services/notification/Dockerfile`
- Update `docker-compose.yml`
- Update database init script

## Phase 8: Update Docker Compose Configuration

### 8.1 Update docker-compose.yml

- Update auth-service: Django, port 8002, auth_db
- Update product-service: Django, port 8003, product_db
- Update order-service: Django, port 8004, order_db
- Add payment-service: Django, port 8005, payment_db
- Add shipping-service: Django, port 8006, shipping_db
- Add notification-service: Django, port 8007, notification_db
- Keep api-gateway as FastAPI/Nginx
- Keep admin-service as FastAPI (can add Django admin later)

### 8.2 Update Environment Variables

- Add database credentials for each service
- Configure JWT secrets
- Setup service-to-service communication URLs
- Configure Stripe keys for payment-service

## Phase 9: Update API Gateway

### 9.1 Update Nginx Configuration

- Add routes for payment-service (`/api/payments/*`)
- Add routes for shipping-service (`/api/shipping/*`)
- Add routes for notification-service (`/api/notifications/*`)
- Update existing routes to point to Django services

### 9.2 Update Gateway Routing

- Ensure all Django services are accessible through gateway
- Configure CORS properly
- Setup rate limiting per service

## Phase 10: Database Schema Updates

### 10.1 Update init-microservices-complete.sql

- Remove old FastAPI tables
- Add Django migration support for each database
- Create separate schemas:
  - `auth_db`: User, VendorProfile, CustomerProfile, Address
  - `product_db`: Product, Category, Brand, ProductImage, ProductVariant, ProductReview, Wishlist
  - `order_db`: Order, OrderItem, Cart, CartItem, Refund, OrderStatusHistory
  - `payment_db`: Payment, PaymentRefund, VendorPayout, Coupon, CouponUsage, SavedPaymentMethod
  - `shipping_db`: ShippingMethod, ShippingZone, Shipment, ShipmentItem, ShipmentTracking, ReturnRequest
  - `notification_db`: Notification, EmailNotification, NotificationPreference, EmailTemplate, SystemAnnouncement

### 10.2 Run Migrations

- Create migration scripts for each service
- Ensure foreign key references work across databases (use user_id instead of FK)

## Phase 11: Inter-Service Communication

### 11.1 Setup Service Discovery

- Create shared service URLs configuration
- Implement HTTP client for service-to-service calls
- Handle user authentication across services (JWT token forwarding)

### 11.2 Update Service Dependencies

- Order service needs Product service (product details)
- Payment service needs Order service (order details)
- Shipping service needs Order service (order items)
- Notification service needs all services (generic FKs)

## Phase 12: Testing and Validation

### 12.1 Test Each Service

- Test auth-service: registration, login, vendor approval
- Test product-service: product CRUD, approval workflow
- Test order-service: cart, order creation, multi-vendor
- Test payment-service: Stripe integration, payouts
- Test shipping-service: shipping calculation, tracking
- Test notification-service: notifications, emails

### 12.2 Integration Testing

- Test complete order flow across services
- Test vendor approval → product creation → order → payment → shipping
- Verify data consistency across databases

## Phase 13: Cleanup

### 13.1 Remove Old Code

- Delete FastAPI auth service code
- Delete FastAPI product service code  
- Delete FastAPI order service code
- Remove unused SQLAlchemy models
- Remove unused Pydantic schemas

### 13.2 Update Documentation

- Update README.md with new Django services
- Update API documentation
- Create migration guide
- Update architecture diagrams

## Key Files to Create/Modify

### New Django Services:

- `services/auth/app/config/settings.py` (Django settings)
- `services/product/app/config/settings.py`
- `services/order/app/config/settings.py`
- `services/payment/app/config/settings.py`
- `services/shipping/app/config/settings.py`
- `services/notification/app/config/settings.py`

### Dockerfiles:

- `services/auth/Dockerfile` (Django)
- `services/product/Dockerfile` (Django)
- `services/order/Dockerfile` (Django)
- `services/payment/Dockerfile` (NEW)
- `services/shipping/Dockerfile` (NEW)
- `services/notification/Dockerfile` (NEW)

### Database:

- Update `database/init-microservices-complete.sql` with all Django models
- Create migration scripts for each service

### Configuration:

- Update `docker-compose.yml` with all new services
- Update `services/gateway/nginx.conf` with new routes

## Important Considerations

1. **Cross-Database Foreign Keys**: Django doesn't support FK across databases. Use `user_id` integers and fetch via API calls or shared user service.

2. **JWT Token Sharing**: All services must validate same JWT tokens. Use shared JWT secret.

3. **Media Files**: Product images, shipping labels need shared storage (S3 or volume mount).

4. **Migrations**: Each Django service runs its own migrations on startup.

5. **Service URLs**: Configure service-to-service communication URLs in environment variables.

6. **Database Users**: Each service has its own database user with appropriate permissions.

## Migration Order

1. Setup Django base structure
2. Migrate auth-service (foundation)
3. Migrate product-service
4. Migrate order-service
5. Create payment-service
6. Create shipping-service
7. Create notification-service
8. Update gateway and compose
9. Test and cleanup