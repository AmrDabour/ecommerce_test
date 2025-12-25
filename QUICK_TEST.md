# Quick Test Guide - Django Microservices

## ✅ Services Status
All Django services are now running! The containers have been rebuilt with proper startup scripts that handle database migrations gracefully.

## 🚀 Quick Test Links

### API Gateway (Port 80)
- **Health Check**: http://localhost/health
- **API Root**: http://localhost/

### Direct Service Access

#### Auth Service (Port 8002) ✅
- **Swagger UI**: http://localhost:8002/swagger/
- **ReDoc**: http://localhost:8002/redoc/
- **Admin Panel**: http://localhost:8002/admin/
- **API**: http://localhost:8002/api/v1/auth/

#### Product Service (Port 8003) ✅
- **Swagger UI**: http://localhost:8003/swagger/
- **ReDoc**: http://localhost:8003/redoc/
- **Admin Panel**: http://localhost:8003/admin/
- **API**: http://localhost:8003/api/v1/products/

#### Order Service (Port 8004) ✅
- **Swagger UI**: http://localhost:8004/swagger/
- **ReDoc**: http://localhost:8004/redoc/
- **Admin Panel**: http://localhost:8004/admin/
- **API**: http://localhost:8004/api/v1/orders/

#### Payment Service (Port 8005) ✅
- **Swagger UI**: http://localhost:8005/swagger/
- **ReDoc**: http://localhost:8005/redoc/
- **Admin Panel**: http://localhost:8005/admin/
- **API**: http://localhost:8005/api/v1/payments/

#### Shipping Service (Port 8006) ✅
- **Swagger UI**: http://localhost:8006/swagger/
- **ReDoc**: http://localhost:8006/redoc/
- **Admin Panel**: http://localhost:8006/admin/
- **API**: http://localhost:8006/api/v1/shipping/

#### Notification Service (Port 8007) ✅
- **Swagger UI**: http://localhost:8007/swagger/
- **ReDoc**: http://localhost:8007/redoc/
- **Admin Panel**: http://localhost:8007/admin/
- **API**: http://localhost:8007/api/v1/notifications/

### Via API Gateway
- **Auth**: http://localhost/api/v1/auth/
- **Accounts**: http://localhost/api/v1/accounts/
- **Products**: http://localhost/api/v1/products/
- **Orders**: http://localhost/api/v1/orders/
- **Payments**: http://localhost/api/v1/payments/
- **Shipping**: http://localhost/api/v1/shipping/
- **Notifications**: http://localhost/api/v1/notifications/

### Database Management
- **Adminer**: http://localhost:8080
  - Server: `postgres`
  - Username: `auth_service` (or other service users)
  - Password: Check docker-compose.yml

## 🧪 Quick Test Commands

```powershell
# Test health check
Invoke-WebRequest -Uri http://localhost/health

# Test auth service
Invoke-WebRequest -Uri http://localhost:8002/api/v1/auth/users/

# Test products via gateway
Invoke-WebRequest -Uri http://localhost/api/v1/products/
```

## 📝 Notes

1. **Static Files**: The "Not Found" messages for CSS/JS files are normal - they're just warnings. The APIs work fine.

2. **Migrations**: The startup scripts automatically handle migrations:
   - First tries `--fake-initial` (for existing tables from SQL script)
   - Falls back to normal migrations if needed

3. **Admin Access**: To access admin panels, you may need to create superusers:
   ```bash
   docker-compose exec auth-service python manage.py createsuperuser
   ```

4. **Database**: Tables already exist from the SQL init script, so migrations are faked on first run.

## ✅ All Services Running with Python 3.11!


