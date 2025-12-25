# 🏗️ E-Commerce Microservices Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Web App  │  │Mobile App│  │  Admin   │  │Third-Party│       │
│  │(React)   │  │(React N.)│  │Dashboard │  │   APIs    │       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬─────┘       │
└────────┼─────────────┼─────────────┼─────────────┼──────────────┘
         │             │             │             │
         └─────────────┴─────────────┴─────────────┘
                              │
    ┌─────────────────────────▼──────────────────────────┐
    │         API GATEWAY (Nginx) - Port 80              │
    │  • Load Balancing                                  │
    │  • Rate Limiting                                   │
    │  • SSL Termination                                 │
    │  • Request Routing                                 │
    └─┬──────────────┬──────────────┬──────────────┬────┘
      │              │              │              │
      │              │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐
│   Auth    │  │ Product  │  │  Order   │  │  Admin   │
│  Service  │  │ Service  │  │ Service  │  │ Service  │
│  Port     │  │  Port    │  │  Port    │  │  Port    │
│  8002     │  │  8003    │  │  8004    │  │  8000    │
└─────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
      │             │              │              │
      │             │              │              │
      │    ┌────────┴──────────────┴──────┐      │
      │    │                               │      │
      │    │   RabbitMQ Message Queue      │      │
      │    │   Port 5672                   │      │
      │    │   • Async Events              │      │
      │    │   • Service Communication     │      │
      │    └───────────────────────────────┘      │
      │                                            │
      │    ┌───────────────────────────────┐      │
      │    │   Redis Cache                 │      │
      │    │   Port 6379                   │      │
      │    │   • Session Storage           │      │
      │    │   • Data Caching              │      │
      │    └───────────────────────────────┘      │
      │                                            │
┌─────▼─────┐  ┌────┬─────┐  ┌────┬─────┐  ┌────▼─────┐
│  auth_db  │  │product_db│  │order_db  │  │ admin_db │
│           │  │          │  │          │  │          │
│ • users   │  │• products│  │• orders  │  │• audit   │
│ • tokens  │  │• categories│ │• payments│  │• logs    │
│ • addresses│ │• reviews │  │• cart    │  │• messages│
└───────────┘  └──────────┘  └──────────┘  └──────────┘
      │             │              │              │
      └─────────────┴──────────────┴──────────────┘
                    │
          ┌─────────▼──────────┐
          │  PostgreSQL 15     │
          │  Port 5432         │
          │  4 Separate DBs    │
          └────────────────────┘
```

## Service Responsibilities

### 1. API Gateway (Nginx)
**Purpose**: Single entry point for all client requests

**Responsibilities**:
- Route requests to appropriate microservices
- Load balancing across service instances
- Rate limiting and throttling
- SSL/TLS termination
- Request logging
- CORS handling at gateway level

**Routing**:
- `/api/auth/*` → Auth Service
- `/api/products/*` → Product Service
- `/api/orders/*` → Order Service
- `/admin/*` → Admin Service

---

### 2. Authentication Service
**Port**: 8002
**Database**: `auth_db`

**Responsibilities**:
- User registration and login
- JWT token generation & validation
- Password management
- User profile management
- Address management
- Role-based access control
- Session management (with Redis)

**Key Endpoints**:
- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh token
- `GET /users/me` - Get profile
- `GET /auth/verify` - Verify token (internal)

**Database Tables**:
- `users` - User accounts
- `addresses` - Shipping/billing addresses
- `refresh_tokens` - JWT refresh tokens

**External Dependencies**:
- Redis (session storage)
- PostgreSQL (auth_db)

---

### 3. Product Service
**Port**: 8003
**Database**: `product_db`

**Responsibilities**:
- Product catalog management
- Category management
- Product search & filtering
- Product reviews & ratings
- Wishlist management
- Inventory tracking

**Planned Endpoints**:
- `GET /products` - List products
- `POST /products` - Create product (seller)
- `GET /products/{id}` - Get product details
- `GET /categories` - List categories
- `POST /products/{id}/reviews` - Add review

**Database Tables**:
- `products` - Product listings
- `categories` - Product categories
- `product_images` - Product photos
- `reviews` - Product reviews
- `wishlist` - User wishlists

**External Dependencies**:
- Auth Service (token verification)
- Redis (product caching)
- RabbitMQ (inventory events)
- PostgreSQL (product_db)

---

### 4. Order Service
**Port**: 8004
**Database**: `order_db`

**Responsibilities**:
- Shopping cart management
- Order creation & processing
- Payment processing (Stripe integration)
- Order tracking
- Coupon/discount management
- Order history

**Planned Endpoints**:
- `POST /cart` - Add to cart
- `GET /cart` - Get cart items
- `POST /orders` - Create order
- `POST /orders/{id}/payment` - Process payment
- `GET /orders/{id}` - Order details

**Database Tables**:
- `orders` - Order records
- `order_items` - Items in orders
- `payments` - Payment transactions
- `cart_items` - Shopping cart
- `coupons` - Discount coupons

**External Dependencies**:
- Auth Service (token verification)
- Product Service (product details)
- Stripe API (payment processing)
- RabbitMQ (order events)
- PostgreSQL (order_db)

---

### 5. Admin Service
**Port**: 8000
**Database**: `admin_db` + READ access to all DBs

**Responsibilities**:
- Admin dashboard (SQLAdmin)
- User management
- Product approval
- Order management
- Analytics & reporting
- System settings
- Audit logging

**Key Features**:
- View all data across services (read-only)
- Admin panel at `/admin`
- User role management
- System configuration

**Database Tables**:
- `audit_logs` - Admin action logs
- `notifications` - User notifications
- `messages` - User-to-user messages
- `system_settings` - App configuration

**External Dependencies**:
- All other service databases (read-only)
- PostgreSQL (admin_db)

---

## Infrastructure Components

### PostgreSQL
**Port**: 5432
**Image**: postgres:15-alpine

**Databases**:
1. `auth_db` - Authentication data
2. `product_db` - Product catalog
3. `order_db` - Orders & payments
4. `admin_db` - Admin & audit data

**Users & Permissions**:
- `ecommerce_admin` - Superuser (for migrations)
- `auth_service` - Full access to auth_db
- `product_service` - Full access to product_db
- `order_service` - Full access to order_db
- `admin_service` - Full access to admin_db, READ-ONLY to others

---

### Redis
**Port**: 6379
**Image**: redis:7-alpine

**Use Cases**:
- Session storage
- JWT token blacklist
- Product catalog caching
- Rate limiting data
- Temporary cart storage

**Configuration**:
- Password protected
- Persistence enabled
- Max memory: 256MB (configurable)

---

### RabbitMQ
**Ports**: 5672 (AMQP), 15672 (Management UI)
**Image**: rabbitmq:3-management-alpine

**Message Queues**:
- `order.created` - New order events
- `product.updated` - Product changes
- `user.registered` - New user events
- `email.notification` - Email queue
- `payment.processed` - Payment events

**Use Cases**:
- Asynchronous order processing
- Email notifications
- Inventory updates
- Event-driven communication

---

## Data Flow Examples

### 1. User Registration Flow
```
Client → API Gateway → Auth Service
                         ↓
                    auth_db (Insert user)
                         ↓
                    RabbitMQ (user.registered event)
                         ↓
                    Email Service (welcome email)
```

### 2. Product Purchase Flow
```
Client → API Gateway → Order Service
                         ↓
                    ┌────┴────┐
                    ↓         ↓
              Auth Service  Product Service
              (verify user) (check stock)
                    ↓
              Payment Gateway (Stripe)
                    ↓
              order_db (create order)
                    ↓
              RabbitMQ (order.created)
                    ↓
         ┌──────────┼──────────┐
         ↓          ↓          ↓
    Inventory  Notification  Email
    Update     Service       Service
```

### 3. Product Search Flow
```
Client → API Gateway → Product Service
                         ↓
                    Redis (check cache)
                         ↓
                    Cache miss?
                         ↓
                    product_db (query)
                         ↓
                    Redis (cache result)
                         ↓
                    Return to client
```

## Security Layers

### 1. API Gateway Layer
- SSL/TLS encryption
- Rate limiting
- DDoS protection
- IP whitelisting (optional)

### 2. Service Layer
- JWT token validation
- Role-based access control
- Request validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

### 3. Database Layer
- User isolation (separate users per service)
- Connection pooling
- Encrypted connections
- Principle of least privilege

### 4. Network Layer
- Docker network isolation
- Service-to-service authentication
- Internal-only services (Redis, RabbitMQ)

## Scalability Strategy

### Horizontal Scaling
```bash
# Scale product service to 3 instances
docker-compose up -d --scale product-service=3

# Scale order service to 2 instances
docker-compose up -d --scale order-service=2
```

### Database Scaling
- Read replicas for heavy read operations
- Database sharding for large datasets
- Connection pooling (already configured)

### Caching Strategy
- Redis for frequently accessed data
- CDN for static assets
- HTTP caching headers

## Monitoring & Observability

### Planned Additions
1. **Prometheus** - Metrics collection
2. **Grafana** - Metrics visualization
3. **ELK Stack** - Log aggregation
4. **Jaeger** - Distributed tracing
5. **Health Checks** - Already implemented

### Current Health Endpoints
- `GET /health` - Each service has health check
- Docker healthchecks configured
- Database connection validation

## Deployment Environments

### Development (Current)
- Docker Compose
- Local environment
- Hot reload enabled
- Debug mode on

### Staging (Recommended)
- Docker Swarm or Kubernetes
- Separate environment variables
- SSL certificates
- Database backups

### Production (Future)
- Kubernetes (EKS, GKE, AKS)
- Auto-scaling groups
- Multi-region deployment
- CDN integration
- Database clustering

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.104.1 |
| Language | Python | 3.11 |
| Database | PostgreSQL | 15 |
| Cache | Redis | 7 |
| Message Queue | RabbitMQ | 3 |
| Gateway | Nginx | Alpine |
| ORM | SQLAlchemy | 2.0.23 |
| Validation | Pydantic | 2.5.0 |
| Authentication | JWT (python-jose) | 3.3.0 |
| Password Hash | bcrypt | 4.2.1 |
| HTTP Client | httpx | 0.25.2 |
| Container | Docker | Latest |
| Orchestration | Docker Compose | 3.8 |

## Inter-Service Communication

### Synchronous (REST)
```python
# Example: Order service calling Auth service
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{AUTH_SERVICE_URL}/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
```

### Asynchronous (RabbitMQ)
```python
# Example: Publishing order created event
await channel.default_exchange.publish(
    Message(json.dumps(order_data).encode()),
    routing_key="order.created"
)
```

## Best Practices Implemented

1. ✅ **Database per Service** - Each service owns its data
2. ✅ **API Gateway Pattern** - Single entry point
3. ✅ **Environment Configuration** - 12-factor app
4. ✅ **Health Checks** - Monitoring readiness
5. ✅ **Security by Default** - JWT, CORS, password hashing
6. ✅ **Dependency Injection** - FastAPI dependencies
7. ✅ **Schema Validation** - Pydantic models
8. ✅ **Connection Pooling** - Database optimization
9. ✅ **Graceful Shutdown** - Container best practices
10. ✅ **Documentation** - Auto-generated API docs

## Future Enhancements

### Phase 1 (Immediate)
- [ ] Complete Product Service implementation
- [ ] Complete Order Service implementation
- [ ] Stripe payment integration

### Phase 2 (Short-term)
- [ ] Email service (SendGrid/SES)
- [ ] File upload service (S3)
- [ ] Search service (Elasticsearch)
- [ ] Notification service

### Phase 3 (Medium-term)
- [ ] Service mesh (Istio/Linkerd)
- [ ] GraphQL gateway (optional)
- [ ] WebSocket service (real-time)
- [ ] Recommendation engine

### Phase 4 (Long-term)
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Monitoring & alerting
- [ ] Multi-region deployment
- [ ] Disaster recovery

---

**This architecture provides a solid foundation for a scalable, maintainable, and secure e-commerce platform.**
