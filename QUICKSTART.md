# 🚀 Quick Start Guide

## Start the Application

```bash
# Navigate to project directory
cd C:\Users\amrda\Downloads\Ecommerce_app

# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f
```

## Access Your Services

✅ **Admin Dashboard**: http://localhost:8000/admin  
✅ **Admin API Docs**: http://localhost:8000/docs  
✅ **REST API**: http://localhost:8001  
✅ **API Docs**: http://localhost:8001/docs  
✅ **Adminer**: http://localhost:8080  

## Default Credentials

### Database (via Adminer)
- System: PostgreSQL
- Server: `postgres`
- Username: `admin`
- Password: `admin`
- Database: `ecommerce_db`

### Admin Dashboard
Create your first admin user through the admin panel.

## Useful Commands

```bash
# Stop all services
docker-compose down

# View service status
docker-compose ps

# Restart a service
docker-compose restart admin

# View logs for specific service
docker-compose logs -f admin
docker-compose logs -f api

# Remove everything including data
docker-compose down -v
```

## Folder Structure Explained

```
Ecommerce_app/
├── services/
│   ├── admin/          → Admin Dashboard Microservice
│   ├── api/            → REST API Microservice
│   └── shared/         → Shared code (models, utils)
├── database/           → Database init and migrations
├── docker-compose.yml  → Orchestration configuration
└── README.md           → Full documentation
```

## Next Steps

1. ✅ Services are running
2. 📊 Create admin user at http://localhost:8000/admin
3. 🛍️ Add products through admin panel
4. 🔌 Test API at http://localhost:8001/docs
5. 📝 Check database at http://localhost:8080

## Troubleshooting

**Port already in use?**
```bash
# Change ports in docker-compose.yml
ports:
  - "8000:8000"  # Change first number only
```

**Database connection failed?**
```bash
# Wait for database to be ready
docker-compose logs postgres

# Restart services
docker-compose restart admin api
```

**Need to reset everything?**
```bash
docker-compose down -v
docker-compose up -d --build
```

---

**Need help?** Check the main [README.md](README.md) for detailed documentation.

