# Multi-Database Admin Setup Guide

## Current Architecture

Your e-commerce platform uses a **microservices architecture** with **4 separate databases**:

1. **`auth_db`** - Users, Addresses
2. **`product_db`** - Products, Categories, Reviews, Cart Items, Wishlist, Coupons
3. **`order_db`** - Orders, Order Items, Payments, Returns, Shipping Events
4. **`admin_db`** - Notifications, Messages, Audit Logs, System Settings

## Why Only 4 Tables Show?

The admin service currently **only connects to `admin_db`**, so you only see:
- Notifications
- Messages  
- Audit Logs
- System Settings

## Solutions to View All Tables

### Option 1: Use API Endpoints (Current Approach)

The admin service already has API endpoints to access data from other services:

- **Users**: `http://localhost:8000/api/users`
- **Products**: `http://localhost:8000/api/products`  
- **Orders**: `http://localhost:8000/api/orders`

These make HTTP calls to the respective microservices.

### Option 2: PostgreSQL Foreign Data Wrapper (FDW) - Recommended

FDW allows you to query tables from other databases as if they were local tables.

#### Setup Steps:

1. **Enable FDW extension in admin_db**:

```sql
-- Connect to admin_db
\c admin_db

-- Enable FDW extension
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
```

2. **Create foreign servers for each database**:

```sql
-- Server for auth_db
CREATE SERVER auth_db_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'auth_db');

-- Server for product_db
CREATE SERVER product_db_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'product_db');

-- Server for order_db
CREATE SERVER order_db_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'order_db');
```

3. **Create user mappings**:

```sql
-- Map admin_service user to access other databases
CREATE USER MAPPING FOR admin_service
SERVER auth_db_server
OPTIONS (user 'admin_service', password 'admin_secure_pass_456!');

CREATE USER MAPPING FOR admin_service
SERVER product_db_server
OPTIONS (user 'admin_service', password 'admin_secure_pass_456!');

CREATE USER MAPPING FOR admin_service
SERVER order_db_server
OPTIONS (user 'admin_service', password 'admin_secure_pass_456!');
```

4. **Import foreign tables**:

```sql
-- Import users table from auth_db
IMPORT FOREIGN SCHEMA public
FROM SERVER auth_db_server
INTO public;

-- Import product tables from product_db
IMPORT FOREIGN SCHEMA public
FROM SERVER product_db_server
INTO public;

-- Import order tables from order_db
IMPORT FOREIGN SCHEMA public
FROM SERVER order_db_server
INTO public;
```

5. **Grant permissions**:

```sql
-- Grant access to admin_service
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO admin_service;
```

After setup, you can query all tables from admin_db:

```sql
-- Query users from auth_db
SELECT * FROM users;

-- Query products from product_db
SELECT * FROM products;

-- Query orders from order_db
SELECT * FROM orders;
```

### Option 3: Use Adminer (Database Management Tool)

You already have Adminer running at `http://localhost:8080`. You can:

1. Connect to each database separately
2. View all tables in each database
3. Switch between databases using the dropdown

**Connection Details:**
- **System**: PostgreSQL
- **Server**: postgres
- **Username**: `ecommerce_admin` (for all DBs) or service-specific users
- **Password**: `change_this_secure_password_123!` (for ecommerce_admin)
- **Database**: Select `auth_db`, `product_db`, `order_db`, or `admin_db`

### Option 4: Modify Admin Service to Use Multiple Engines

This requires creating separate Admin instances for each database and mounting them at different paths (e.g., `/admin/auth`, `/admin/products`, `/admin/orders`).

## Recommended Approach

For **development**: Use **Adminer** to browse all databases.

For **production**: Set up **Foreign Data Wrappers (FDW)** so the admin panel can access all tables seamlessly.

## Quick Check: What Tables Exist Where?

Run this in PostgreSQL to see all tables:

```sql
-- Check auth_db tables
\c auth_db
\dt

-- Check product_db tables  
\c product_db
\dt

-- Check order_db tables
\c order_db
\dt

-- Check admin_db tables
\c admin_db
\dt
```

Or use Adminer to browse each database visually!



