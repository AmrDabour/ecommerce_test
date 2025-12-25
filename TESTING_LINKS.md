# Testing Links for E-Commerce Microservices

## 🌐 API Gateway (Port 80)
All services are accessible through the API Gateway:

### Health Check
- **Health**: http://localhost/health

### API Endpoints (via Gateway)

#### Authentication & Accounts
- **Auth API**: http://localhost/api/v1/auth/
- **Accounts API**: http://localhost/api/v1/accounts/
- **Swagger Docs**: http://localhost:8002/swagger/
- **ReDoc Docs**: http://localhost:8002/redoc/

#### Products
- **Products API**: http://localhost/api/v1/products/
- **Swagger Docs**: http://localhost:8003/swagger/
- **ReDoc Docs**: http://localhost:8003/redoc/

#### Orders
- **Orders API**: http://localhost/api/v1/orders/
- **Swagger Docs**: http://localhost:8004/swagger/
- **ReDoc Docs**: http://localhost:8004/redoc/

#### Payments
- **Payments API**: http://localhost/api/v1/payments/
- **Swagger Docs**: http://localhost:8005/swagger/
- **ReDoc Docs**: http://localhost:8005/redoc/

#### Shipping
- **Shipping API**: http://localhost/api/v1/shipping/
- **ReDoc Docs**: http://localhost:8006/redoc/

#### Notifications
- **Notifications API**: http://localhost/api/v1/notifications/
- **Swagger Docs**: http://localhost:8007/swagger/
- **ReDoc Docs**: http://localhost:8007/redoc/

---

## 🔗 Direct Service Access (Development)

### Auth Service (Port 8002)
- **Base URL**: http://localhost:8002
- **Admin Panel**: http://localhost:8002/admin/
- **Swagger**: http://localhost:8002/swagger/
- **ReDoc**: http://localhost:8002/redoc/
- **API**: http://localhost:8002/api/v1/auth/
- **Accounts**: http://localhost:8002/api/v1/accounts/

### Product Service (Port 8003)
- **Base URL**: http://localhost:8003
- **Admin Panel**: http://localhost:8003/admin/
- **Swagger**: http://localhost:8003/swagger/
- **ReDoc**: http://localhost:8003/redoc/
- **API**: http://localhost:8003/api/v1/products/

### Order Service (Port 8004)
- **Base URL**: http://localhost:8004
- **Admin Panel**: http://localhost:8004/admin/
- **Swagger**: http://localhost:8004/swagger/
- **ReDoc**: http://localhost:8004/redoc/
- **API**: http://localhost:8004/api/v1/orders/

### Payment Service (Port 8005)
- **Base URL**: http://localhost:8005
- **Admin Panel**: http://localhost:8005/admin/
- **Swagger**: http://localhost:8005/swagger/
- **ReDoc**: http://localhost:8005/redoc/
- **API**: http://localhost:8005/api/v1/payments/

### Shipping Service (Port 8006)
- **Base URL**: http://localhost:8006
- **Admin Panel**: http://localhost:8006/admin/
- **Swagger**: http://localhost:8006/swagger/
- **ReDoc**: http://localhost:8006/redoc/
- **API**: http://localhost:8006/api/v1/shipping/

### Notification Service (Port 8007)
- **Base URL**: http://localhost:8007
- **Admin Panel**: http://localhost:8007/admin/
- **Swagger**: http://localhost:8007/swagger/
- **ReDoc**: http://localhost:8007/redoc/
- **API**: http://localhost:8007/api/v1/notifications/

---

## 🛠️ Admin Tools

### Adminer (Database Management)
- **URL**: http://localhost:8080
- **Server**: postgres
- **Username**: ecommerce_admin (or service-specific users)
- **Password**: Check docker-compose.yml or .env file

### Admin Dashboard
- **URL**: http://localhost:8000/admin/ (if admin service is FastAPI)
- **URL**: http://localhost/admin/ (via gateway)

---

## 🧪 Quick Test Commands

### Test Health Check
```bash
curl http://localhost/health
```

### Test Auth Service
```bash
curl http://localhost:8002/api/v1/auth/users/me/
```

### Test Product Service
```bash
curl http://localhost:8003/api/v1/products/
```

### Test Order Service
```bash
curl http://localhost:8004/api/v1/orders/
```

### Test via Gateway
```bash
curl http://localhost/api/v1/products/
curl http://localhost/api/v1/auth/users/
```

---

## 📝 Important Notes

1. **First Time Setup**: You'll need to run migrations and create superusers:
   ```bash
   # Run migrations for each service
   docker-compose exec auth-service python manage.py migrate
   docker-compose exec product-service python manage.py migrate
   docker-compose exec order-service python manage.py migrate
   docker-compose exec payment-service python manage.py migrate
   docker-compose exec shipping-service python manage.py migrate
   docker-compose exec notification-service python manage.py migrate
   
   # Create superuser (optional, for admin access)
   docker-compose exec auth-service python manage.py createsuperuser
   ```

2. **Authentication**: Most endpoints require JWT authentication. Get a token from:
   - `POST http://localhost/api/v1/auth/jwt/create/` with username/password

3. **CORS**: Make sure your frontend origin is in `ALLOWED_ORIGINS` environment variable

4. **Database**: Use Adminer (http://localhost:8080) to inspect databases directly

---

## 🔍 Check Service Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f auth-service
docker-compose logs -f product-service
docker-compose logs -f order-service
```

---

## ✅ Expected Responses

### Health Check
```json
healthy
```

### API Gateway Root
```json
{
  "message": "E-Commerce API Gateway",
  "version": "1.0.0"
}
```

### Swagger UI
- Should show interactive API documentation
- Can test endpoints directly from the browser


