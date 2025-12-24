# 🛒 E-Commerce Microservices Platform

A modern, scalable e-commerce platform built with microservices architecture, FastAPI, PostgreSQL, and Docker.

## 📁 Project Structure

```
Ecommerce_app/
├── services/
│   ├── admin/                  # Admin Dashboard Service
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py        # FastAPI application
│   │   │   ├── admin_views.py  # SQLAdmin views
│   │   │   └── config.py       # Configuration
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── api/                    # REST API Service
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── routes/         # API routes
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── shared/                 # Shared resources
│       ├── __init__.py
│       └── models.py           # SQLAlchemy models
├── database/
│   ├── init.sql                # Database initialization
│   └── migrations/             # Database migrations
├── config/                     # Configuration files
├── docs/                       # Documentation
├── docker-compose.yml          # Docker orchestration
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Docker Compose

### 1. Start All Services

```bash
# Build and start all microservices
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f admin
docker-compose logs -f api
```

### 2. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Admin Dashboard** | http://localhost:8000/admin | Management interface |
| **Admin API Docs** | http://localhost:8000/docs | Admin API documentation |
| **REST API** | http://localhost:8001 | Public API |
| **API Documentation** | http://localhost:8001/docs | API documentation |
| **Adminer** | http://localhost:8080 | Database management |
| **PostgreSQL** | localhost:5432 | Database server |

### 3. Adminer Database Access

- **System**: PostgreSQL
- **Server**: postgres
- **Username**: admin
- **Password**: admin
- **Database**: ecommerce_db

## 🏗️ Microservices Architecture

### Admin Service (`services/admin/`)
- **Port**: 8000
- **Purpose**: Admin dashboard for managing the e-commerce platform
- **Features**:
  - User management
  - Product catalog management
  - Order processing
  - Analytics and reporting
  - Content management

### API Service (`services/api/`)
- **Port**: 8001
- **Purpose**: REST API for frontend applications and third-party integrations
- **Features**:
  - Product listings
  - Shopping cart
  - Order processing
  - User authentication
  - Payment processing

### Shared Resources (`services/shared/`)
- **Purpose**: Common code shared across services
- **Contents**:
  - Database models (SQLAlchemy)
  - Utilities
  - Constants

## 🔧 Development

### Running Services Locally

Each service can run independently for development:

#### Admin Service
```bash
cd services/admin/app
pip install -r ../requirements.txt
python main.py
```

#### API Service
```bash
cd services/api/app
pip install -r ../requirements.txt
python main.py
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DB_HOST=postgres
DB_USER=admin
DB_PASSWORD=admin
DB_NAME=ecommerce_db
DB_PORT=5432

# Services
ADMIN_PORT=8000
API_PORT=8001
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop and remove all data
docker-compose down -v

# Restart a specific service
docker-compose restart admin
docker-compose restart api

# Scale a service
docker-compose up -d --scale api=3
```

## 📊 Database Schema

The platform includes the following database tables:

- **users** - User accounts (buyers, sellers, admins)
- **categories** - Product categories
- **products** - Product listings
- **product_images** - Product images
- **orders** - Customer orders
- **order_items** - Items in orders
- **payments** - Payment transactions
- **addresses** - Shipping/billing addresses
- **reviews** - Product reviews
- **cart_items** - Shopping cart
- **wishlist** - User wishlists
- **messages** - User messages
- **coupons** - Discount coupons
- **notifications** - User notifications

## 🔐 Security Features

- ✅ Password hashing with bcrypt
- ✅ Environment-based configuration
- ✅ Docker container isolation
- ✅ Database connection pooling
- ✅ Health checks for all services

## 📈 Scalability

The microservices architecture allows for:

- **Horizontal Scaling**: Scale individual services based on demand
- **Independent Deployment**: Deploy services without affecting others
- **Technology Flexibility**: Use different tech stacks for different services
- **Fault Isolation**: Failures in one service don't crash the entire system

## 🧪 Testing

```bash
# Run tests for admin service
cd services/admin
pytest

# Run tests for API service
cd services/api
pytest
```

## 📝 API Documentation

- **Admin API**: http://localhost:8000/docs
- **Public API**: http://localhost:8001/docs

Both services use FastAPI's automatic interactive documentation (Swagger UI).

## 🌐 Production Deployment

### Using Docker Swarm

```bash
docker swarm init
docker stack deploy -c docker-compose.yml ecommerce
```

### Using Kubernetes

```bash
# Coming soon...
```

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **Admin**: SQLAdmin
- **Authentication**: Passlib + bcrypt
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Web Server**: Uvicorn

## 📚 Additional Documentation

- [API Documentation](./docs/api.md)
- [Database Schema](./docs/database.md)
- [Deployment Guide](./docs/deployment.md)
- [Contributing Guide](./docs/contributing.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👥 Team

Built with ❤️ by the E-Commerce Team

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Contact: support@ecommerce.com

---

**Happy coding!** 🚀

