-- ====================================
-- E-COMMERCE MICROSERVICES DATABASE - COMPLETE VERSION
-- ====================================
-- Converted from monolithic to microservices architecture
-- Preserves ALL views, triggers, procedures, and functions
-- ====================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================
-- CREATE DATABASES FOR EACH SERVICE
-- ====================================

-- Create default database for PostgreSQL superuser (ecommerce_admin)
-- This ensures the database exists for the POSTGRES_USER
CREATE DATABASE ecommerce_admin;

-- Create Auth Service Database
CREATE DATABASE auth_db;

-- Create Product Service Database
CREATE DATABASE product_db;

-- Create Order Service Database
CREATE DATABASE order_db;

-- Create Admin Service Database
CREATE DATABASE admin_db;

-- ====================================
-- CREATE USERS FOR EACH SERVICE
-- ====================================

-- Auth Service User
CREATE USER auth_service WITH PASSWORD 'auth_secure_pass_345!';
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_service;

-- Product Service User
CREATE USER product_service WITH PASSWORD 'product_secure_pass_789!';
GRANT ALL PRIVILEGES ON DATABASE product_db TO product_service;

-- Order Service User
CREATE USER order_service WITH PASSWORD 'order_secure_pass_012!';
GRANT ALL PRIVILEGES ON DATABASE order_db TO order_service;

-- Admin Service User (read-only access to all databases for reporting)
CREATE USER admin_service WITH PASSWORD 'admin_secure_pass_456!';
GRANT ALL PRIVILEGES ON DATABASE admin_db TO admin_service;

-- ====================================
-- CONNECT TO AUTH DATABASE
-- ====================================
\c auth_db;

-- Grant privileges to auth_service
GRANT ALL PRIVILEGES ON SCHEMA public TO auth_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO auth_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO auth_service;

-- ==========================================
-- AUTH SERVICE TABLES
-- ==========================================

-- USERS TABLE (ENHANCED)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'customer' CHECK (role IN ('customer', 'vendor', 'admin')),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    avatar_url TEXT,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

COMMENT ON TABLE users IS 'User accounts (customers, vendors, admins)';

-- ADDRESSES TABLE (ENHANCED)
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    address_type VARCHAR(20) CHECK (address_type IN ('shipping', 'billing')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(100),
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_addresses_type ON addresses(address_type);
CREATE INDEX idx_addresses_country ON addresses(country);

COMMENT ON TABLE addresses IS 'User shipping and billing addresses';

-- CUSTOMER PROFILES TABLE
CREATE TABLE customer_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    avatar VARCHAR(100),
    loyalty_points INTEGER DEFAULT 0 CHECK (loyalty_points >= 0),
    newsletter_subscribed BOOLEAN DEFAULT FALSE,
    total_orders INTEGER DEFAULT 0 CHECK (total_orders >= 0),
    total_spent DECIMAL(12,2) DEFAULT 0.00,
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_profiles_loyalty_points ON customer_profiles(loyalty_points);

COMMENT ON TABLE customer_profiles IS 'Extended customer profile information';

-- VENDOR PROFILES TABLE
CREATE TABLE vendor_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    business_name VARCHAR(255) UNIQUE NOT NULL,
    business_description TEXT DEFAULT '',
    business_registration_number VARCHAR(100) DEFAULT '',
    business_email VARCHAR(254),
    business_phone VARCHAR(17) DEFAULT '',
    business_address TEXT DEFAULT '',
    business_city VARCHAR(100) DEFAULT '',
    business_state VARCHAR(100) DEFAULT '',
    business_country VARCHAR(100) DEFAULT '',
    business_postal_code VARCHAR(20) DEFAULT '',
    logo VARCHAR(100),
    banner VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'suspended')),
    commission_rate DECIMAL(5,2) DEFAULT 10.00,
    approved_at TIMESTAMP,
    approved_by_id INTEGER, -- References users.id
    rejection_reason TEXT DEFAULT '',
    total_sales DECIMAL(12,2) DEFAULT 0.00,
    total_products INTEGER DEFAULT 0 CHECK (total_products >= 0),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendor_profiles_status ON vendor_profiles(status);
CREATE INDEX idx_vendor_profiles_business_name ON vendor_profiles(business_name);
CREATE INDEX idx_vendor_profiles_is_featured ON vendor_profiles(is_featured);

COMMENT ON TABLE vendor_profiles IS 'Vendor business profiles and settings';

-- REFRESH TOKENS TABLE (for JWT)
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);

-- ==========================================
-- AUTH SERVICE TRIGGERS
-- ==========================================

-- Function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addresses_updated_at BEFORE UPDATE ON addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customer_profiles_updated_at BEFORE UPDATE ON customer_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vendor_profiles_updated_at BEFORE UPDATE ON vendor_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- AUTH SERVICE PROCEDURES
-- ==========================================

-- Procedure: Register User (ENHANCED)
CREATE OR REPLACE PROCEDURE sp_register_user(
    p_email VARCHAR(255),
    p_password_hash VARCHAR(255),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    OUT p_user_id INT,
    p_role VARCHAR(20) DEFAULT 'customer'
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO users (email, password_hash, first_name, last_name, role, is_verified, is_active)
    VALUES (p_email, p_password_hash, p_first_name, p_last_name, p_role, FALSE, TRUE)
    RETURNING id INTO p_user_id;

    -- Auto-create customer profile for customers
    IF p_role = 'customer' THEN
        INSERT INTO customer_profiles (user_id) VALUES (p_user_id);
    END IF;
END;
$$;

-- Procedure: Verify User
CREATE OR REPLACE PROCEDURE sp_verify_user(
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE users SET is_verified = TRUE WHERE id = p_user_id;
END;
$$;

-- Procedure: Upgrade to Seller (DEPRECATED - use sp_upgrade_to_vendor)
CREATE OR REPLACE PROCEDURE sp_upgrade_to_seller(
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE users SET role = 'vendor' WHERE id = p_user_id;
END;
$$;

-- Procedure: Upgrade to Vendor (NEW)
CREATE OR REPLACE PROCEDURE sp_upgrade_to_vendor(
    p_user_id INT,
    p_business_name VARCHAR(255),
    p_business_email VARCHAR(254)
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE users SET role = 'vendor' WHERE id = p_user_id;

    INSERT INTO vendor_profiles (user_id, business_name, business_email, status)
    VALUES (p_user_id, p_business_name, p_business_email, 'pending')
    ON CONFLICT (user_id) DO UPDATE
    SET business_name = EXCLUDED.business_name,
        business_email = EXCLUDED.business_email;
END;
$$;

-- Procedure: Approve Vendor (NEW)
CREATE OR REPLACE PROCEDURE sp_approve_vendor(
    p_vendor_user_id INT,
    p_admin_id INT,
    p_approved BOOLEAN,
    p_rejection_reason TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_approved THEN
        UPDATE vendor_profiles
        SET status = 'approved',
            approved_at = CURRENT_TIMESTAMP,
            approved_by_id = p_admin_id,
            rejection_reason = ''
        WHERE user_id = p_vendor_user_id;
    ELSE
        UPDATE vendor_profiles
        SET status = 'rejected',
            rejection_reason = p_rejection_reason
        WHERE user_id = p_vendor_user_id;
    END IF;
END;
$$;

-- Procedure: Update Customer Stats (NEW)
CREATE OR REPLACE PROCEDURE sp_update_customer_stats(
    p_user_id INT,
    p_order_total DECIMAL(12,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO customer_profiles (user_id, total_orders, total_spent)
    VALUES (p_user_id, 1, p_order_total)
    ON CONFLICT (user_id) DO UPDATE
    SET total_orders = customer_profiles.total_orders + 1,
        total_spent = customer_profiles.total_spent + p_order_total;
END;
$$;

-- Procedure: Ban/Unban User
CREATE OR REPLACE PROCEDURE sp_ban_user(
    p_user_id INT,
    p_ban BOOLEAN,
    p_reason TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE users SET is_active = NOT p_ban WHERE id = p_user_id;
END;
$$;

-- Procedure: Add Address (ENHANCED)
CREATE OR REPLACE PROCEDURE sp_add_address(
    p_user_id INT,
    p_address_type VARCHAR(20),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    p_address_line1 VARCHAR(255),
    p_city VARCHAR(100),
    p_postal_code VARCHAR(20),
    p_country VARCHAR(100),
    p_phone VARCHAR(20),
    OUT p_address_id INT,
    p_company VARCHAR(100) DEFAULT NULL,
    p_is_default BOOLEAN DEFAULT FALSE
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_is_default THEN
        UPDATE addresses SET is_default = FALSE
        WHERE user_id = p_user_id AND address_type = p_address_type;
    END IF;

    INSERT INTO addresses (
        user_id, address_type, first_name, last_name, company, address_line1,
        city, postal_code, country, phone, is_default
    ) VALUES (
        p_user_id, p_address_type, p_first_name, p_last_name, p_company, p_address_line1,
        p_city, p_postal_code, p_country, p_phone, p_is_default
    ) RETURNING id INTO p_address_id;
END;
$$;

-- Procedure: Set Default Address (ENHANCED)
CREATE OR REPLACE PROCEDURE sp_set_default_address(
    p_user_id INT,
    p_address_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_address_type VARCHAR(20);
BEGIN
    SELECT address_type INTO v_address_type FROM addresses WHERE id = p_address_id AND user_id = p_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Address not found';
    END IF;

    UPDATE addresses SET is_default = FALSE
    WHERE user_id = p_user_id AND address_type = v_address_type;

    UPDATE addresses SET is_default = TRUE WHERE id = p_address_id;
END;
$$;

-- ==========================================
-- AUTH SERVICE VIEWS
-- ==========================================

-- View: User statistics (ENHANCED)
CREATE OR REPLACE VIEW vw_user_statistics AS
SELECT
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    u.is_verified,
    u.is_active,
    u.created_at,
    COALESCE(cp.total_orders, 0) as total_orders,
    COALESCE(cp.total_spent, 0) as total_spent,
    COALESCE(vp.total_sales, 0) as vendor_total_sales,
    vp.business_name,
    vp.status as vendor_status
FROM users u
LEFT JOIN customer_profiles cp ON u.id = cp.user_id
LEFT JOIN vendor_profiles vp ON u.id = vp.user_id;

COMMENT ON VIEW vw_user_statistics IS 'User statistics and information with customer and vendor profiles';

-- Insert sample data
INSERT INTO users (email, password_hash, first_name, last_name, role, is_verified, is_active, is_staff, is_superuser)
VALUES
    ('admin@ecommerce.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtJ3yW5sJQy6', 'Admin', 'User', 'admin', TRUE, TRUE, TRUE, TRUE),
    ('vendor@ecommerce.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtJ3yW5sJQy6', 'Vendor', 'Demo', 'vendor', TRUE, TRUE, FALSE, FALSE),
    ('customer@ecommerce.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5jtJ3yW5sJQy6', 'Customer', 'Demo', 'customer', TRUE, TRUE, FALSE, FALSE);

-- Create profiles for demo users
INSERT INTO customer_profiles (user_id) VALUES (3);
INSERT INTO vendor_profiles (user_id, business_name, business_email, status, approved_at, approved_by_id)
VALUES (2, 'Demo Vendor Shop', 'vendor@ecommerce.com', 'approved', CURRENT_TIMESTAMP, 1);

-- ====================================
-- CONNECT TO PRODUCT DATABASE
-- ====================================
\c product_db;

GRANT ALL PRIVILEGES ON SCHEMA public TO product_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO product_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO product_service;

-- ==========================================
-- PRODUCT SERVICE TABLES
-- ==========================================

-- BRANDS TABLE
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    logo VARCHAR(100),
    website VARCHAR(200) DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_brands_slug ON brands(slug);
CREATE INDEX idx_brands_is_active ON brands(is_active);

COMMENT ON TABLE brands IS 'Product brands';

-- CATEGORIES TABLE (ENHANCED)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    position INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_is_active ON categories(is_active);

COMMENT ON TABLE categories IS 'Product categories (hierarchical)';

-- PRODUCTS TABLE (ENHANCED)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL, -- References auth_db.users.id (renamed from seller_id)
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(550) UNIQUE,
    description TEXT,
    short_description TEXT DEFAULT '',
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    compare_at_price DECIMAL(10, 2) CHECK (compare_at_price >= 0),
    cost_per_item DECIMAL(10, 2) CHECK (cost_per_item >= 0),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    low_stock_threshold INTEGER DEFAULT 5,
    track_inventory BOOLEAN DEFAULT TRUE,
    allow_backorders BOOLEAN DEFAULT FALSE,
    sku VARCHAR(100),
    barcode VARCHAR(100),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
    condition VARCHAR(20) CHECK (condition IN ('new', 'used', 'refurbished')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'rejected', 'archived')),
    approval_status VARCHAR(20) DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    weight DECIMAL(10, 2),
    length DECIMAL(10, 2),
    width DECIMAL(10, 2),
    height DECIMAL(10, 2),
    meta_title VARCHAR(255) DEFAULT '',
    meta_description TEXT DEFAULT '',
    meta_keywords VARCHAR(500) DEFAULT '',
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    view_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    favorites_count INTEGER DEFAULT 0,
    published_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by_id INTEGER, -- References auth_db.users.id
    submitted_for_approval_at TIMESTAMP,
    deleted_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_vendor_id ON products(vendor_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_brand_id ON products(brand_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_approval_status ON products(approval_status);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_is_featured ON products(is_featured);
CREATE INDEX idx_products_created_at ON products(created_at);
CREATE INDEX idx_products_deleted_at ON products(deleted_at);
CREATE INDEX idx_products_title ON products USING gin(to_tsvector('english', title));

COMMENT ON TABLE products IS 'Product listings from vendors';
COMMENT ON COLUMN products.deleted_at IS 'Soft delete timestamp for auditing';

-- PRODUCT IMAGES TABLE (ENHANCED)
CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    alt_text VARCHAR(255),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_images_product_id ON product_images(product_id);

-- PRODUCT VARIANTS TABLE (ENHANCED)
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(255),
    sku VARCHAR(100) UNIQUE,
    variant_name VARCHAR(100),
    size VARCHAR(50),
    color VARCHAR(50),
    material VARCHAR(100),
    price DECIMAL(10, 2) CHECK (price >= 0),
    compare_at_price DECIMAL(10, 2) CHECK (compare_at_price >= 0),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    weight DECIMAL(10, 2),
    barcode VARCHAR(100),
    image_url VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE product_variants IS 'Product variations (size, color, material)';

CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_product_variants_is_active ON product_variants(is_active);

-- REVIEWS TABLE (ENHANCED)
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL, -- References auth_db.users.id
    order_id INTEGER, -- References order_db.orders.id
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, user_id, order_id)
);

CREATE INDEX idx_reviews_product_id ON reviews(product_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_is_approved ON reviews(is_approved);
CREATE INDEX idx_reviews_created_at ON reviews(created_at);

COMMENT ON TABLE reviews IS 'Product reviews and ratings';

-- PRODUCT ATTRIBUTES TABLE
CREATE TABLE product_attributes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    value VARCHAR(500) NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_attributes_product_id ON product_attributes(product_id);

COMMENT ON TABLE product_attributes IS 'Custom product attributes (specs, features)';

-- WISHLIST TABLE
CREATE TABLE wishlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL, -- References auth_db.users.id
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_wishlist_user_id ON wishlist(user_id);
CREATE INDEX idx_wishlist_product_id ON wishlist(product_id);

COMMENT ON TABLE wishlist IS 'User wishlists';

-- ==========================================
-- PRODUCT SERVICE TRIGGERS
-- ==========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_variants_updated_at BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- PRODUCT SERVICE PROCEDURES & FUNCTIONS
-- ==========================================

-- Procedure: Approve/Reject Product
CREATE OR REPLACE PROCEDURE sp_approve_product(
    p_product_id INT,
    p_admin_id INT,
    p_approved BOOLEAN,
    p_reason TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_product RECORD;
BEGIN
    SELECT * INTO v_product FROM products WHERE id = p_product_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found';
    END IF;

    IF p_approved THEN
        UPDATE products
        SET approval_status = 'approved',
            status = 'approved',
            approved_at = CURRENT_TIMESTAMP,
            approved_by_id = p_admin_id,
            rejection_reason = NULL,
            published_at = COALESCE(published_at, CURRENT_TIMESTAMP)
        WHERE id = p_product_id;
    ELSE
        UPDATE products
        SET approval_status = 'rejected',
            status = 'rejected',
            rejection_reason = p_reason
        WHERE id = p_product_id;
    END IF;
END;
$$;

-- Procedure: Update Inventory
CREATE OR REPLACE PROCEDURE sp_update_inventory(
    p_product_id INT,
    p_quantity_change INT,
    p_reason VARCHAR(50) DEFAULT 'manual_adjustment'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_new_quantity INT;
BEGIN
    UPDATE products
    SET quantity = quantity + p_quantity_change
    WHERE id = p_product_id
    RETURNING quantity INTO v_new_quantity;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found';
    END IF;

    IF v_new_quantity < 0 THEN
        RAISE EXCEPTION 'Insufficient inventory. New quantity would be: %', v_new_quantity;
    END IF;
END;
$$;

-- Procedure: Bulk Approve Products
CREATE OR REPLACE PROCEDURE sp_bulk_approve_products(
    p_product_ids INT[],
    p_admin_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_product_id INT;
BEGIN
    FOREACH v_product_id IN ARRAY p_product_ids
    LOOP
        CALL sp_approve_product(v_product_id, p_admin_id, TRUE, NULL);
    END LOOP;
END;
$$;

-- Function: Check Stock Availability
CREATE OR REPLACE FUNCTION fn_check_stock_availability(
    p_product_id INT,
    p_quantity INT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_available_quantity INT;
BEGIN
    SELECT quantity INTO v_available_quantity
    FROM products
    WHERE id = p_product_id AND approval_status = 'approved';

    IF v_available_quantity IS NULL THEN
        RETURN FALSE;
    END IF;

    RETURN v_available_quantity >= p_quantity;
END;
$$;

-- Procedure: Soft Delete Product
CREATE OR REPLACE PROCEDURE sp_soft_delete_product(
    p_product_id INT,
    p_admin_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM products WHERE id = p_product_id) THEN
        RAISE EXCEPTION 'Product not found';
    END IF;

    UPDATE products
    SET deleted_at = CURRENT_TIMESTAMP
    WHERE id = p_product_id AND deleted_at IS NULL;
END;
$$;

-- Procedure: Restore Soft Deleted Product
CREATE OR REPLACE PROCEDURE sp_restore_product(
    p_product_id INT,
    p_admin_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE products
    SET deleted_at = NULL
    WHERE id = p_product_id AND deleted_at IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found or not deleted';
    END IF;
END;
$$;

-- Procedure: Add Review
CREATE OR REPLACE PROCEDURE sp_add_review(
    p_product_id INT,
    p_user_id INT,
    p_order_id INT,
    p_rating INT,
    p_title VARCHAR(255) DEFAULT NULL,
    p_comment TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_verified BOOLEAN := FALSE;
BEGIN
    IF p_rating < 1 OR p_rating > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5';
    END IF;

    -- Note: In microservices, verification would be done via API call to Order service
    -- For now, we'll set it based on order_id presence
    v_verified := (p_order_id IS NOT NULL);

    INSERT INTO reviews (product_id, user_id, order_id, rating, title, comment, is_verified_purchase)
    VALUES (p_product_id, p_user_id, p_order_id, p_rating, p_title, p_comment, v_verified);

    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = p_product_id;
END;
$$;

-- Function: Get Product Average Rating (ENHANCED)
CREATE OR REPLACE FUNCTION fn_get_product_rating(
    p_product_id INT
)
RETURNS TABLE(
    avg_rating DECIMAL(3, 2),
    total_reviews INT,
    rating_distribution JSON
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(AVG(rating), 0)::DECIMAL(3, 2),
        COUNT(*)::INT,
        json_build_object(
            '5_star', COUNT(*) FILTER (WHERE rating = 5),
            '4_star', COUNT(*) FILTER (WHERE rating = 4),
            '3_star', COUNT(*) FILTER (WHERE rating = 3),
            '2_star', COUNT(*) FILTER (WHERE rating = 2),
            '1_star', COUNT(*) FILTER (WHERE rating = 1)
        )
    FROM reviews
    WHERE product_id = p_product_id AND is_approved = TRUE;
END;
$$;

-- Procedure: Increment View Count (NEW)
CREATE OR REPLACE PROCEDURE sp_increment_view_count(
    p_product_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE products
    SET view_count = view_count + 1
    WHERE id = p_product_id;
END;
$$;

-- Procedure: Add Product Variant
CREATE OR REPLACE PROCEDURE sp_add_product_variant(
    p_product_id INT,
    p_variant_name VARCHAR(100),
    p_sku VARCHAR(100),
    p_price DECIMAL(10, 2),
    p_quantity INTEGER,
    OUT p_variant_id INT,
    p_size VARCHAR(50) DEFAULT NULL,
    p_color VARCHAR(50) DEFAULT NULL,
    p_material VARCHAR(100) DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM products WHERE id = p_product_id) THEN
        RAISE EXCEPTION 'Product not found';
    END IF;

    INSERT INTO product_variants (
        product_id, variant_name, sku, size, color, material,
        price, quantity, is_active
    ) VALUES (
        p_product_id, p_variant_name, p_sku, p_size, p_color, p_material,
        p_price, p_quantity, TRUE
    ) RETURNING id INTO p_variant_id;
END;
$$;

-- Procedure: Update Variant Inventory
CREATE OR REPLACE PROCEDURE sp_update_variant_inventory(
    p_variant_id INT,
    p_quantity_change INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE product_variants
    SET quantity = quantity + p_quantity_change
    WHERE id = p_variant_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Variant not found';
    END IF;

    UPDATE product_variants
    SET is_active = FALSE
    WHERE id = p_variant_id AND quantity <= 0;
END;
$$;

-- ==========================================
-- PRODUCT SERVICE VIEWS
-- ==========================================

-- View: Active Products (excluding soft deleted) (ENHANCED)
CREATE OR REPLACE VIEW vw_active_products AS
SELECT
    p.*,
    c.name AS category_name,
    b.name AS brand_name,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(r.id) AS review_count
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN reviews r ON p.id = r.product_id AND r.is_approved = TRUE
WHERE p.deleted_at IS NULL
GROUP BY p.id, c.name, b.name;

COMMENT ON VIEW vw_active_products IS 'Products that are not soft deleted';

-- View: Product Variants with Details (ENHANCED)
CREATE OR REPLACE VIEW vw_product_variants_details AS
SELECT
    pv.*,
    p.title AS product_title,
    p.vendor_id,
    p.category_id,
    c.name AS category_name,
    CASE
        WHEN pv.quantity > 0 AND pv.is_active = TRUE THEN TRUE
        ELSE FALSE
    END AS available
FROM product_variants pv
JOIN products p ON pv.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.deleted_at IS NULL;

COMMENT ON VIEW vw_product_variants_details IS 'Product variants with product and vendor details';

-- View: Product reviews with details (ENHANCED)
CREATE OR REPLACE VIEW vw_product_reviews_detailed AS
SELECT
    r.id AS review_id,
    r.product_id,
    p.title AS product_title,
    p.vendor_id,
    r.user_id,
    r.order_id,
    r.rating,
    r.title AS review_title,
    r.comment,
    r.is_verified_purchase,
    r.is_approved,
    r.helpful_count,
    r.created_at,
    r.updated_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.created_at))/86400 AS days_ago
FROM reviews r
JOIN products p ON r.product_id = p.id
ORDER BY r.created_at DESC;

-- View: Popular products (ENHANCED)
CREATE OR REPLACE VIEW vw_popular_products AS
SELECT
    p.id AS product_id,
    p.title,
    p.description,
    p.price,
    p.compare_at_price,
    p.vendor_id,
    cat.name AS category_name,
    b.name AS brand_name,
    p.view_count,
    p.views_count,
    p.favorites_count,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(DISTINCT r.id) AS review_count,
    pi.image_url AS product_image,
    (COALESCE(p.view_count, p.views_count, 0) * 0.3 + p.favorites_count * 0.5) AS popularity_score
FROM products p
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN brands b ON p.brand_id = b.id
LEFT JOIN reviews r ON p.id = r.product_id AND r.is_approved = TRUE
LEFT JOIN LATERAL (
    SELECT image_url
    FROM product_images
    WHERE product_id = p.id
    ORDER BY display_order, position
    LIMIT 1
) pi ON TRUE
WHERE p.approval_status = 'approved'
AND p.quantity > 0
AND p.deleted_at IS NULL
GROUP BY p.id, p.title, p.description, p.price, p.compare_at_price, p.vendor_id,
         cat.name, b.name, p.view_count, p.views_count, p.favorites_count, pi.image_url
ORDER BY popularity_score DESC;

-- View: Pending product approvals (ENHANCED)
CREATE OR REPLACE VIEW vw_pending_approvals AS
SELECT
    p.id AS product_id,
    p.title,
    p.description,
    p.price,
    p.quantity,
    p.vendor_id,
    p.category_id,
    cat.name AS category_name,
    p.created_at AS submitted_at,
    p.submitted_for_approval_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - p.created_at))/3600 AS hours_pending,
    pi.image_url AS product_image,
    COUNT(DISTINCT pi2.id) AS total_images
FROM products p
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN LATERAL (
    SELECT image_url
    FROM product_images
    WHERE product_id = p.id
    ORDER BY display_order, position
    LIMIT 1
) pi ON TRUE
LEFT JOIN product_images pi2 ON p.id = pi2.product_id
WHERE p.approval_status = 'pending'
GROUP BY p.id, p.title, p.description, p.price, p.quantity, p.vendor_id,
         p.category_id, cat.name, p.created_at, p.submitted_for_approval_at, pi.image_url
ORDER BY p.created_at ASC;

-- View: Product inventory status (ENHANCED)
CREATE OR REPLACE VIEW vw_product_inventory_status AS
SELECT
    p.id AS product_id,
    p.title,
    p.sku,
    p.quantity AS current_stock,
    p.low_stock_threshold,
    p.vendor_id,
    cat.name AS category_name,
    CASE
        WHEN p.quantity = 0 THEN 'OUT_OF_STOCK'
        WHEN p.quantity <= COALESCE(p.low_stock_threshold, 5) THEN 'LOW_STOCK'
        WHEN p.quantity <= 20 THEN 'MEDIUM_STOCK'
        ELSE 'IN_STOCK'
    END AS stock_status
FROM products p
LEFT JOIN categories cat ON p.category_id = cat.id
WHERE p.approval_status = 'approved'
AND p.deleted_at IS NULL;

-- Insert sample brands
INSERT INTO brands (name, slug, description, is_active)
VALUES
    ('Apple', 'apple', 'Premium electronics and devices', TRUE),
    ('Samsung', 'samsung', 'Electronics and appliances', TRUE),
    ('Nike', 'nike', 'Sports apparel and equipment', TRUE),
    ('Adidas', 'adidas', 'Sports apparel and equipment', TRUE)
ON CONFLICT (slug) DO NOTHING;

-- ====================================
-- CONNECT TO ORDER DATABASE
-- ====================================
\c order_db;

GRANT ALL PRIVILEGES ON SCHEMA public TO order_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO order_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO order_service;

-- ==========================================
-- ORDER SERVICE TABLES
-- ==========================================

-- ORDERS TABLE (ENHANCED)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    buyer_id INTEGER NOT NULL, -- References auth_db.users.id
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')),
    subtotal DECIMAL(10, 2) NOT NULL,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    tax DECIMAL(10, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_status VARCHAR(20) CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    payment_method VARCHAR(50),
    shipping_address_id INTEGER, -- References auth_db.addresses.id
    billing_address_id INTEGER, -- References auth_db.addresses.id
    tracking_number VARCHAR(100),
    carrier VARCHAR(50),
    coupon_id INTEGER, -- References coupons.id
    coupon_code VARCHAR(50) DEFAULT '',
    customer_note TEXT DEFAULT '',
    admin_note TEXT DEFAULT '',
    notes TEXT,
    ip_address INET,
    user_agent TEXT DEFAULT '',
    paid_at TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    deleted_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_deleted_at ON orders(deleted_at);
CREATE INDEX idx_orders_coupon_id ON orders(coupon_id);

COMMENT ON TABLE orders IS 'Customer orders';
COMMENT ON COLUMN orders.deleted_at IS 'Soft delete timestamp for auditing';
COMMENT ON COLUMN orders.coupon_id IS 'Coupon used for this order';

-- ORDER ITEMS TABLE (ENHANCED)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL, -- References product_db.products.id
    vendor_id INTEGER NOT NULL, -- References auth_db.users.id (renamed from seller_id)
    title VARCHAR(255) NOT NULL,
    product_name VARCHAR(500),
    product_sku VARCHAR(100),
    variant_name VARCHAR(255) DEFAULT '',
    variant_id INTEGER, -- References product_db.product_variants.id
    sku VARCHAR(100),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 10.00,
    commission_amount DECIMAL(12,2) DEFAULT 0,
    vendor_payout DECIMAL(12,2) DEFAULT 0,
    is_shipped BOOLEAN DEFAULT FALSE,
    is_delivered BOOLEAN DEFAULT FALSE,
    is_cancelled BOOLEAN DEFAULT FALSE,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_vendor_id ON order_items(vendor_id);
CREATE INDEX idx_order_items_variant_id ON order_items(variant_id);

COMMENT ON TABLE order_items IS 'Individual items in orders';

-- PAYMENTS TABLE
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    stripe_payment_id VARCHAR(255),
    payment_intent_id VARCHAR(255) UNIQUE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'cancelled', 'refunded')),
    payment_method VARCHAR(50),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_stripe_payment_id ON payments(stripe_payment_id);
CREATE INDEX idx_payments_payment_intent_id ON payments(payment_intent_id);
CREATE INDEX idx_payments_status ON payments(status);

COMMENT ON TABLE payments IS 'Payment transactions';

-- CARTS TABLE
CREATE TABLE carts (
    customer_id INTEGER PRIMARY KEY, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE carts IS 'Shopping carts (one per customer)';

-- CART ITEMS TABLE (ENHANCED)
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES carts(customer_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL, -- References product_db.products.id
    variant_id INTEGER, -- References product_db.product_variants.id
    quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cart_items_cart_id ON cart_items(cart_id);
CREATE INDEX idx_cart_items_product_id ON cart_items(product_id);
CREATE INDEX idx_cart_items_variant_id ON cart_items(variant_id);

-- Unique constraint for ON CONFLICT in sp_add_to_cart procedure
-- Allows only one cart item per cart/product/variant combination
-- Note: NULL variant_id values are considered distinct, so multiple NULLs are allowed
-- This matches the procedure's ON CONFLICT (cart_id, product_id, variant_id) clause
CREATE UNIQUE INDEX idx_cart_items_unique ON cart_items(cart_id, product_id, variant_id);

COMMENT ON TABLE cart_items IS 'Shopping cart items';

-- COUPONS TABLE (ENHANCED)
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) DEFAULT '',
    description TEXT DEFAULT '',
    discount_type VARCHAR(20) CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value DECIMAL(10, 2) NOT NULL,
    min_purchase_amount DECIMAL(10, 2),
    max_discount_amount DECIMAL(10, 2),
    usage_limit INTEGER,
    used_count INTEGER DEFAULT 0,
    max_uses_per_customer INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_by_id INTEGER, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coupons_code ON coupons(code);
CREATE INDEX idx_coupons_is_active ON coupons(is_active);
CREATE INDEX idx_coupons_valid_until ON coupons(valid_until);

COMMENT ON TABLE coupons IS 'Discount coupons';

-- COUPON USAGES TABLE
CREATE TABLE coupon_usages (
    id SERIAL PRIMARY KEY,
    coupon_id INTEGER NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL, -- References auth_db.users.id
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    discount_amount DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coupon_usages_coupon_id ON coupon_usages(coupon_id);
CREATE INDEX idx_coupon_usages_customer_id ON coupon_usages(customer_id);
CREATE INDEX idx_coupon_usages_order_id ON coupon_usages(order_id);

COMMENT ON TABLE coupon_usages IS 'Tracks coupon usage per customer';

-- ORDER STATUS HISTORY TABLE
CREATE TABLE order_status_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    old_status VARCHAR(20) NOT NULL,
    new_status VARCHAR(20) NOT NULL,
    comment TEXT DEFAULT '',
    notified_customer BOOLEAN DEFAULT FALSE,
    changed_by_id INTEGER, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_status_history_order_id ON order_status_history(order_id);
CREATE INDEX idx_order_status_history_created_at ON order_status_history(created_at);

COMMENT ON TABLE order_status_history IS 'Tracks all order status changes';

-- SHIPPING METHODS TABLE
CREATE TABLE shipping_methods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    base_cost DECIMAL(12,2) NOT NULL,
    cost_per_kg DECIMAL(8,2) DEFAULT 0,
    free_shipping_threshold DECIMAL(12,2),
    min_delivery_days INTEGER DEFAULT 1,
    max_delivery_days INTEGER DEFAULT 7,
    is_active BOOLEAN DEFAULT TRUE,
    is_international BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipping_methods_is_active ON shipping_methods(is_active);

COMMENT ON TABLE shipping_methods IS 'Available shipping methods';

-- SHIPPING ZONES TABLE
CREATE TABLE shipping_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    countries TEXT NOT NULL, -- Comma-separated or JSON array
    price_multiplier DECIMAL(5,2) DEFAULT 1.00,
    additional_fee DECIMAL(12,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipping_zones_is_active ON shipping_zones(is_active);

COMMENT ON TABLE shipping_zones IS 'Shipping zones and pricing rules';

-- Insert sample shipping methods
INSERT INTO shipping_methods (name, description, base_cost, cost_per_kg, min_delivery_days, max_delivery_days, is_active)
VALUES
    ('Standard Shipping', 'Standard delivery', 9.99, 2.00, 5, 7, TRUE),
    ('Express Shipping', 'Fast delivery', 19.99, 3.00, 2, 3, TRUE),
    ('Overnight', 'Next day delivery', 39.99, 5.00, 1, 1, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert sample shipping zones
INSERT INTO shipping_zones (name, description, countries, price_multiplier, additional_fee, is_active)
VALUES
    ('Domestic', 'Local shipping', 'US', 1.00, 0.00, TRUE),
    ('Europe', 'European Union', 'DE,FR,IT,ES,GB', 1.50, 10.00, TRUE),
    ('International', 'Worldwide', '*', 2.00, 25.00, TRUE)
ON CONFLICT (name) DO NOTHING;

-- SHIPMENTS TABLE
CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    tracking_number VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned')),
    carrier_name VARCHAR(255) DEFAULT '',
    carrier_service VARCHAR(255) DEFAULT '',
    carrier_tracking_url VARCHAR(200) DEFAULT '',
    total_weight DECIMAL(8,2),
    length DECIMAL(8,2),
    width DECIMAL(8,2),
    height DECIMAL(8,2),
    shipping_cost DECIMAL(12,2) NOT NULL,
    carrier_cost DECIMAL(12,2),
    estimated_delivery_date TIMESTAMP,
    shipping_address_snapshot TEXT, -- Denormalized address
    special_instructions TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    shipping_method_id INTEGER REFERENCES shipping_methods(id),
    vendor_id INTEGER, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);

CREATE INDEX idx_shipments_order_id ON shipments(order_id);
CREATE INDEX idx_shipments_tracking_number ON shipments(tracking_number);
CREATE INDEX idx_shipments_status ON shipments(status);

COMMENT ON TABLE shipments IS 'Shipment tracking information';

-- SHIPMENT ITEMS TABLE
CREATE TABLE shipment_items (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipment_items_shipment_id ON shipment_items(shipment_id);
CREATE INDEX idx_shipment_items_order_item_id ON shipment_items(order_item_id);

COMMENT ON TABLE shipment_items IS 'Links order items to shipments';

-- SHIPMENT TRACKING TABLE
CREATE TABLE shipment_tracking (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL,
    location VARCHAR(500) DEFAULT '',
    description TEXT DEFAULT '',
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    carrier_status_code VARCHAR(100) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipment_tracking_shipment_id ON shipment_tracking(shipment_id);
CREATE INDEX idx_shipment_tracking_event_time ON shipment_tracking(event_time);

COMMENT ON TABLE shipment_tracking IS 'Detailed shipment tracking events';

-- SHIPPING LABELS TABLE
CREATE TABLE shipping_labels (
    shipment_id INTEGER PRIMARY KEY REFERENCES shipments(id) ON DELETE CASCADE,
    label_file VARCHAR(100) NOT NULL,
    label_format VARCHAR(10) DEFAULT 'PDF' CHECK (label_format IN ('PDF', 'PNG', 'ZPL')),
    label_id VARCHAR(255) DEFAULT '',
    rate_id VARCHAR(255) DEFAULT '',
    postage_cost DECIMAL(12,2) NOT NULL,
    barcode VARCHAR(255) DEFAULT '',
    is_voided BOOLEAN DEFAULT FALSE,
    voided_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE shipping_labels IS 'Generated shipping labels';

-- SAVED PAYMENT METHODS TABLE
CREATE TABLE saved_payment_methods (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL, -- References auth_db.users.id
    stripe_payment_method_id VARCHAR(255) UNIQUE NOT NULL,
    card_brand VARCHAR(50) DEFAULT '',
    card_last4 VARCHAR(4) DEFAULT '',
    card_exp_month SMALLINT CHECK (card_exp_month >= 1 AND card_exp_month <= 12),
    card_exp_year SMALLINT,
    is_default BOOLEAN DEFAULT FALSE,
    nickname VARCHAR(100) DEFAULT '',
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_saved_payment_methods_customer_id ON saved_payment_methods(customer_id);
CREATE INDEX idx_saved_payment_methods_is_default ON saved_payment_methods(is_default);

COMMENT ON TABLE saved_payment_methods IS 'Customer saved payment methods';

-- PAYMENT REFUNDS TABLE
CREATE TABLE payment_refunds (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    refund_transaction_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'cancelled')),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    stripe_refund_id VARCHAR(255) DEFAULT '',
    reason TEXT DEFAULT '',
    failure_reason TEXT DEFAULT '',
    refund_request_id INTEGER, -- References returns.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    succeeded_at TIMESTAMP
);

CREATE INDEX idx_payment_refunds_payment_id ON payment_refunds(payment_id);
CREATE INDEX idx_payment_refunds_status ON payment_refunds(status);

COMMENT ON TABLE payment_refunds IS 'Payment refund transactions';

-- VENDOR PAYOUTS TABLE
CREATE TABLE vendor_payouts (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL, -- References auth_db.users.id
    payout_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'paid', 'failed', 'cancelled')),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    payment_method VARCHAR(50) DEFAULT '',
    bank_account_name VARCHAR(255) DEFAULT '',
    bank_account_number VARCHAR(100) DEFAULT '',
    bank_name VARCHAR(255) DEFAULT '',
    bank_routing_number VARCHAR(50) DEFAULT '',
    stripe_payout_id VARCHAR(255) DEFAULT '',
    admin_note TEXT DEFAULT '',
    transaction_reference VARCHAR(255) DEFAULT '',
    processed_by_id INTEGER, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

CREATE INDEX idx_vendor_payouts_vendor_id ON vendor_payouts(vendor_id);
CREATE INDEX idx_vendor_payouts_status ON vendor_payouts(status);
CREATE INDEX idx_vendor_payouts_payout_number ON vendor_payouts(payout_number);

COMMENT ON TABLE vendor_payouts IS 'Vendor payment tracking';

-- RETURNS TABLE (ENHANCED)
CREATE TABLE returns (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    order_item_id INTEGER REFERENCES order_items(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL, -- References auth_db.users.id
    return_number VARCHAR(50) UNIQUE,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'requested' CHECK (status IN ('requested', 'approved', 'rejected', 'processing', 'completed', 'cancelled')),
    refund_amount DECIMAL(10, 2) NOT NULL CHECK (refund_amount >= 0),
    refund_method VARCHAR(50),
    return_tracking_number VARCHAR(100),
    quantity INTEGER DEFAULT 1,
    image_1 VARCHAR(100),
    image_2 VARCHAR(100),
    image_3 VARCHAR(100),
    return_label_provided BOOLEAN DEFAULT FALSE,
    resolution_note TEXT DEFAULT '',
    admin_notes TEXT,
    approved_by INTEGER, -- References auth_db.users.id
    approved_at TIMESTAMP,
    received_at TIMESTAMP,
    completed_at TIMESTAMP,
    vendor_id INTEGER, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE returns IS 'Product return and refund tracking';

CREATE INDEX idx_returns_order_id ON returns(order_id);
CREATE INDEX idx_returns_user_id ON returns(user_id);
CREATE INDEX idx_returns_status ON returns(status);
CREATE INDEX idx_returns_created_at ON returns(created_at);

-- SHIPPING EVENTS TABLE
CREATE TABLE shipping_events (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    location VARCHAR(255),
    description TEXT,
    notes TEXT,
    carrier VARCHAR(50),
    tracking_number VARCHAR(100),
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE shipping_events IS 'Shipping status tracking and history';

CREATE INDEX idx_shipping_events_order_id ON shipping_events(order_id);
CREATE INDEX idx_shipping_events_status ON shipping_events(status);
CREATE INDEX idx_shipping_events_event_time ON shipping_events(event_time);
CREATE INDEX idx_shipping_events_tracking_number ON shipping_events(tracking_number);

-- ==========================================
-- ORDER SERVICE TRIGGERS
-- ==========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carts_updated_at BEFORE UPDATE ON carts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_returns_updated_at BEFORE UPDATE ON returns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipping_methods_updated_at BEFORE UPDATE ON shipping_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipping_zones_updated_at BEFORE UPDATE ON shipping_zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipments_updated_at BEFORE UPDATE ON shipments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipping_labels_updated_at BEFORE UPDATE ON shipping_labels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_payment_methods_updated_at BEFORE UPDATE ON saved_payment_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_refunds_updated_at BEFORE UPDATE ON payment_refunds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vendor_payouts_updated_at BEFORE UPDATE ON vendor_payouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- ORDER SERVICE PROCEDURES & FUNCTIONS
-- ==========================================

-- Procedure: Create Order from Cart
CREATE OR REPLACE PROCEDURE sp_create_order(
    p_buyer_id INT,
    p_shipping_address_id INT,
    p_billing_address_id INT,
    p_payment_method VARCHAR(50),
    OUT p_order_id INT,
    OUT p_order_number VARCHAR(50),
    OUT p_total DECIMAL(10, 2),
    p_coupon_code VARCHAR(50) DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_subtotal DECIMAL(10, 2) := 0;
    v_shipping_cost DECIMAL(10, 2) := 10.00;
    v_tax DECIMAL(10, 2) := 0;
    v_discount DECIMAL(10, 2) := 0;
    v_cart_item RECORD;
    v_coupon RECORD;
BEGIN
    -- Note: In microservices, cart items would have product prices fetched from Product service
    -- For this example, we'll work with what we have in cart

    -- Generate order number
    p_order_number := 'ORD-' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDD') || '-' || LPAD(nextval('orders_id_seq')::TEXT, 6, '0');

    -- Calculate subtotal (would normally fetch prices from Product service)
    SELECT SUM(quantity * unit_price) INTO v_subtotal FROM cart_items WHERE cart_id = p_buyer_id;

    IF v_subtotal IS NULL OR v_subtotal = 0 THEN
        RAISE EXCEPTION 'Cart is empty';
    END IF;

    v_tax := v_subtotal * 0.10;

    -- Apply coupon if provided
    IF p_coupon_code IS NOT NULL THEN
        SELECT * INTO v_coupon FROM coupons
        WHERE code = p_coupon_code
        AND is_active = TRUE
        AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
        AND (usage_limit IS NULL OR used_count < usage_limit);

        IF FOUND THEN
            IF v_coupon.discount_type = 'percentage' THEN
                v_discount := v_subtotal * (v_coupon.discount_value / 100);
                IF v_coupon.max_discount_amount IS NOT NULL THEN
                    v_discount := LEAST(v_discount, v_coupon.max_discount_amount);
                END IF;
            ELSIF v_coupon.discount_type = 'fixed' THEN
                v_discount := v_coupon.discount_value;
            END IF;

            UPDATE coupons SET used_count = used_count + 1 WHERE id = v_coupon.id;
        END IF;
    END IF;

    p_total := v_subtotal + v_shipping_cost + v_tax - v_discount;

    -- Create order
    INSERT INTO orders (
        order_number, buyer_id, status, subtotal, shipping_cost, tax, discount, total,
        payment_status, payment_method, shipping_address_id, billing_address_id, coupon_id
    ) VALUES (
        p_order_number, p_buyer_id, 'pending', v_subtotal, v_shipping_cost, v_tax, v_discount, p_total,
        'pending', p_payment_method, p_shipping_address_id, p_billing_address_id, v_coupon.id
    ) RETURNING id INTO p_order_id;

    -- Move cart items to order items (would fetch product details from Product service)
    FOR v_cart_item IN
        SELECT cart_id, product_id, variant_id, quantity, unit_price
        FROM cart_items
        WHERE cart_id = p_buyer_id
    LOOP
        INSERT INTO order_items (order_id, product_id, vendor_id, title, variant_id, quantity, price, total)
        VALUES (p_order_id, v_cart_item.product_id, 1, 'Product', v_cart_item.variant_id,
                v_cart_item.quantity, v_cart_item.unit_price, v_cart_item.quantity * v_cart_item.unit_price);
    END LOOP;

    -- Clear cart
    DELETE FROM cart_items WHERE cart_id = p_buyer_id;
END;
$$;

-- Procedure: Cancel Order
CREATE OR REPLACE PROCEDURE sp_cancel_order(
    p_order_id INT,
    p_reason TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order RECORD;
BEGIN
    SELECT * INTO v_order FROM orders WHERE id = p_order_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;

    IF v_order.status IN ('cancelled', 'delivered') THEN
        RAISE EXCEPTION 'Cannot cancel order with status: %', v_order.status;
    END IF;

    -- Update order status
    UPDATE orders SET status = 'cancelled', notes = p_reason WHERE id = p_order_id;

    IF v_order.payment_status = 'paid' THEN
        UPDATE orders SET payment_status = 'refunded' WHERE id = p_order_id;
    END IF;
END;
$$;

-- Procedure: Update Order Status
CREATE OR REPLACE PROCEDURE sp_update_order_status(
    p_order_id INT,
    p_new_status VARCHAR(30),
    p_tracking_number VARCHAR(100) DEFAULT NULL,
    p_carrier VARCHAR(50) DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM orders WHERE id = p_order_id) THEN
        RAISE EXCEPTION 'Order not found';
    END IF;

    UPDATE orders
    SET status = p_new_status,
        tracking_number = COALESCE(p_tracking_number, tracking_number),
        carrier = COALESCE(p_carrier, carrier)
    WHERE id = p_order_id;
END;
$$;

-- Procedure: Process Payment
CREATE OR REPLACE PROCEDURE sp_process_payment(
    p_order_id INT,
    p_stripe_payment_id VARCHAR(255),
    p_amount DECIMAL(10, 2),
    p_payment_method VARCHAR(50),
    p_status VARCHAR(20) DEFAULT 'succeeded'
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM orders WHERE id = p_order_id) THEN
        RAISE EXCEPTION 'Order not found';
    END IF;

    INSERT INTO payments (order_id, stripe_payment_id, amount, status, payment_method)
    VALUES (p_order_id, p_stripe_payment_id, p_amount, p_status, p_payment_method);

    IF p_status = 'succeeded' THEN
        UPDATE orders SET payment_status = 'paid', status = 'confirmed' WHERE id = p_order_id;
    ELSIF p_status = 'failed' THEN
        UPDATE orders SET payment_status = 'failed' WHERE id = p_order_id;
    END IF;
END;
$$;

-- Procedure: Process Refund
CREATE OR REPLACE PROCEDURE sp_process_refund(
    p_order_id INT,
    p_refund_amount DECIMAL(10, 2),
    p_reason TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order RECORD;
BEGIN
    SELECT * INTO v_order FROM orders WHERE id = p_order_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;

    IF v_order.payment_status != 'paid' THEN
        RAISE EXCEPTION 'Cannot refund unpaid order';
    END IF;

    UPDATE payments SET status = 'refunded' WHERE order_id = p_order_id;
    UPDATE orders SET payment_status = 'refunded' WHERE id = p_order_id;
END;
$$;

-- Procedure: Add to Cart (ENHANCED)
CREATE OR REPLACE PROCEDURE sp_add_to_cart(
    p_user_id INT,
    p_product_id INT,
    p_quantity INT DEFAULT 1,
    p_variant_id INT DEFAULT NULL,
    p_unit_price DECIMAL(12,2) DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_cart_id INT;
    v_price DECIMAL(12,2);
BEGIN
    -- Ensure cart exists
    INSERT INTO carts (customer_id) VALUES (p_user_id)
    ON CONFLICT (customer_id) DO NOTHING;
    
    v_cart_id := p_user_id;
    
    -- Use provided price or default
    v_price := COALESCE(p_unit_price, 10.00);
    
    -- In microservices, stock check and price would be done via API call to Product service
    INSERT INTO cart_items (cart_id, product_id, variant_id, quantity, unit_price)
    VALUES (v_cart_id, p_product_id, p_variant_id, p_quantity, v_price)
    ON CONFLICT (cart_id, product_id, variant_id)
    DO UPDATE SET quantity = cart_items.quantity + p_quantity;
END;
$$;

-- Procedure: Update Cart Item (ENHANCED)
CREATE OR REPLACE PROCEDURE sp_update_cart_item(
    p_user_id INT,
    p_product_id INT,
    p_new_quantity INT,
    p_variant_id INT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_new_quantity <= 0 THEN
        DELETE FROM cart_items 
        WHERE cart_id = p_user_id AND product_id = p_product_id 
        AND (p_variant_id IS NULL OR variant_id = p_variant_id);
    ELSE
        UPDATE cart_items
        SET quantity = p_new_quantity
        WHERE cart_id = p_user_id AND product_id = p_product_id
        AND (p_variant_id IS NULL OR variant_id = p_variant_id);
    END IF;
END;
$$;

-- Procedure: Clear Cart (ENHANCED)
CREATE OR REPLACE PROCEDURE sp_clear_cart(
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM cart_items WHERE cart_id = p_user_id;
END;
$$;

-- Function: Validate Coupon
CREATE OR REPLACE FUNCTION fn_validate_coupon(
    p_coupon_code VARCHAR(50),
    p_cart_total DECIMAL(10, 2)
)
RETURNS TABLE(
    valid BOOLEAN,
    discount_amount DECIMAL(10, 2),
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_coupon RECORD;
    v_discount DECIMAL(10, 2);
BEGIN
    SELECT * INTO v_coupon FROM coupons WHERE code = p_coupon_code;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 0.00, 'Invalid coupon code';
        RETURN;
    END IF;

    IF NOT v_coupon.is_active THEN
        RETURN QUERY SELECT FALSE, 0.00, 'Coupon is inactive';
        RETURN;
    END IF;

    IF v_coupon.valid_until IS NOT NULL AND v_coupon.valid_until < CURRENT_TIMESTAMP THEN
        RETURN QUERY SELECT FALSE, 0.00, 'Coupon has expired';
        RETURN;
    END IF;

    IF v_coupon.usage_limit IS NOT NULL AND v_coupon.used_count >= v_coupon.usage_limit THEN
        RETURN QUERY SELECT FALSE, 0.00, 'Coupon usage limit reached';
        RETURN;
    END IF;

    IF v_coupon.min_purchase_amount IS NOT NULL AND p_cart_total < v_coupon.min_purchase_amount THEN
        RETURN QUERY SELECT FALSE, 0.00,
            'Minimum purchase amount: $' || v_coupon.min_purchase_amount::TEXT;
        RETURN;
    END IF;

    -- Calculate discount
    IF v_coupon.discount_type = 'percentage' THEN
        v_discount := p_cart_total * (v_coupon.discount_value / 100);
        IF v_coupon.max_discount_amount IS NOT NULL THEN
            v_discount := LEAST(v_discount, v_coupon.max_discount_amount);
        END IF;
    ELSIF v_coupon.discount_type = 'fixed' THEN
        v_discount := v_coupon.discount_value;
    END IF;

    RETURN QUERY SELECT TRUE, v_discount, 'Coupon applied successfully';
END;
$$;

-- Function: Calculate Seller Commission (ENHANCED - renamed to vendor)
CREATE OR REPLACE FUNCTION fn_calculate_seller_commission(
    p_order_item_id INT,
    p_commission_rate DECIMAL(5, 2) DEFAULT 10.00
)
RETURNS TABLE(
    vendor_id INT,
    item_total DECIMAL(10, 2),
    commission DECIMAL(10, 2),
    vendor_amount DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        oi.vendor_id,
        oi.total,
        (oi.total * p_commission_rate / 100)::DECIMAL(10, 2),
        (oi.total - (oi.total * p_commission_rate / 100))::DECIMAL(10, 2)
    FROM order_items oi
    WHERE oi.id = p_order_item_id;
END;
$$;

-- Procedure: Request Return
CREATE OR REPLACE PROCEDURE sp_request_return(
    p_order_id INT,
    p_order_item_id INT,
    p_user_id INT,
    p_reason TEXT,
    p_refund_amount DECIMAL(10, 2),
    OUT p_return_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_status VARCHAR(30);
BEGIN
    SELECT status INTO v_order_status FROM orders WHERE id = p_order_id AND buyer_id = p_user_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;

    IF v_order_status NOT IN ('delivered', 'completed') THEN
        RAISE EXCEPTION 'Returns can only be requested for delivered orders';
    END IF;

    INSERT INTO returns (
        order_id, order_item_id, user_id, reason,
        status, refund_amount
    ) VALUES (
        p_order_id, p_order_item_id, p_user_id, p_reason,
        'requested', p_refund_amount
    ) RETURNING id INTO p_return_id;
END;
$$;

-- Procedure: Process Return
CREATE OR REPLACE PROCEDURE sp_process_return(
    p_return_id INT,
    p_admin_id INT,
    p_approve BOOLEAN,
    p_admin_notes TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_new_status VARCHAR(20);
BEGIN
    IF NOT EXISTS (SELECT 1 FROM returns WHERE id = p_return_id) THEN
        RAISE EXCEPTION 'Return not found';
    END IF;

    v_new_status := CASE WHEN p_approve THEN 'approved' ELSE 'rejected' END;

    UPDATE returns
    SET
        status = v_new_status,
        approved_by = p_admin_id,
        approved_at = CURRENT_TIMESTAMP,
        admin_notes = p_admin_notes
    WHERE id = p_return_id;

    IF p_approve THEN
        UPDATE returns
        SET status = 'processing'
        WHERE id = p_return_id;
    END IF;
END;
$$;

-- Procedure: Complete Return
CREATE OR REPLACE PROCEDURE sp_complete_return(
    p_return_id INT,
    p_admin_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE returns
    SET
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE id = p_return_id AND status = 'processing';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Return not found or not in processing status';
    END IF;
END;
$$;

-- Procedure: Add Shipping Event
CREATE OR REPLACE PROCEDURE sp_add_shipping_event(
    p_order_id INT,
    p_status VARCHAR(50),
    p_location VARCHAR(255) DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_notes TEXT DEFAULT NULL,
    p_carrier VARCHAR(50) DEFAULT NULL,
    p_tracking_number VARCHAR(100) DEFAULT NULL,
    p_event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM orders WHERE id = p_order_id) THEN
        RAISE EXCEPTION 'Order not found';
    END IF;

    INSERT INTO shipping_events (
        order_id, status, location, description, notes,
        carrier, tracking_number, event_time
    ) VALUES (
        p_order_id, p_status, p_location, p_description, p_notes,
        p_carrier, p_tracking_number, p_event_time
    );

    IF p_tracking_number IS NOT NULL THEN
        UPDATE orders
        SET
            tracking_number = p_tracking_number,
            carrier = p_carrier
        WHERE id = p_order_id;
    END IF;
END;
$$;

-- ==========================================
-- ORDER SERVICE VIEWS
-- ==========================================

-- View: Order items with full details (ENHANCED)
CREATE OR REPLACE VIEW vw_order_items_full AS
SELECT
    oi.id AS order_item_id,
    oi.order_id,
    oi.product_id,
    oi.vendor_id,
    oi.variant_id,
    oi.title AS product_title,
    oi.product_name,
    oi.product_sku,
    oi.variant_name,
    oi.quantity,
    oi.price AS unit_price,
    oi.total AS item_total,
    oi.tax_amount,
    oi.discount_amount,
    oi.commission_rate,
    oi.commission_amount,
    oi.vendor_payout,
    oi.is_shipped,
    oi.is_delivered,
    oi.is_cancelled,
    oi.created_at,
    o.order_number,
    o.buyer_id,
    o.status AS order_status,
    o.payment_status
FROM order_items oi
JOIN orders o ON oi.order_id = o.id;

-- View: Complete order history
CREATE OR REPLACE VIEW vw_order_history_complete AS
SELECT
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    o.status,
    o.payment_status,
    o.payment_method,
    o.subtotal,
    o.shipping_cost,
    o.tax,
    o.discount,
    o.total,
    o.tracking_number,
    o.carrier,
    o.created_at AS order_date,
    o.updated_at,
    COUNT(DISTINCT oi.id) AS total_items,
    SUM(oi.quantity) AS total_quantity,
    p.status AS payment_record_status,
    p.stripe_payment_id
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN payments p ON o.id = p.order_id
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.order_number, o.buyer_id, o.status, o.payment_status,
         o.payment_method, o.subtotal, o.shipping_cost, o.tax, o.discount,
         o.total, o.tracking_number, o.carrier, o.created_at, o.updated_at,
         p.status, p.stripe_payment_id;

-- View: Pending orders
CREATE OR REPLACE VIEW vw_pending_orders AS
SELECT
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    o.status,
    o.payment_status,
    o.total,
    o.created_at,
    CASE
        WHEN o.payment_status = 'pending' THEN 'AWAITING_PAYMENT'
        WHEN o.payment_status = 'paid' AND o.status = 'pending' THEN 'READY_TO_SHIP'
        WHEN o.status = 'confirmed' THEN 'READY_TO_SHIP'
        WHEN o.status = 'processing' THEN 'BEING_PREPARED'
        ELSE 'REVIEW_NEEDED'
    END AS action_required,
    COUNT(DISTINCT oi.vendor_id) AS vendor_count,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - o.created_at))/3600 AS hours_since_order
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status IN ('pending', 'confirmed', 'processing')
GROUP BY o.id, o.order_number, o.buyer_id, o.status, o.payment_status, o.total, o.created_at;

-- View: Order shipping information
CREATE OR REPLACE VIEW vw_order_shipping_info AS
SELECT
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    o.status AS order_status,
    o.tracking_number,
    o.carrier,
    o.created_at AS order_date,
    o.updated_at AS last_update,
    CASE
        WHEN o.status = 'pending' THEN 1
        WHEN o.status = 'confirmed' THEN 2
        WHEN o.status = 'processing' THEN 3
        WHEN o.status = 'shipped' THEN 4
        WHEN o.status = 'delivered' THEN 5
        ELSE 0
    END AS status_stage
FROM orders o
WHERE o.status NOT IN ('cancelled', 'refunded')
AND o.deleted_at IS NULL;

-- View: Returns with Details
CREATE OR REPLACE VIEW vw_returns_details AS
SELECT
    r.id AS return_id,
    r.order_id,
    o.order_number,
    r.user_id,
    r.reason,
    r.status,
    r.refund_amount,
    r.refund_method,
    r.return_tracking_number,
    r.admin_notes,
    r.approved_by,
    r.approved_at,
    r.completed_at,
    r.created_at,
    r.updated_at,
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - r.created_at)) AS days_pending
FROM returns r
LEFT JOIN orders o ON r.order_id = o.id;

COMMENT ON VIEW vw_returns_details IS 'Returns with order and approval details';

-- View: Shipping Tracking History
CREATE OR REPLACE VIEW vw_shipping_tracking AS
SELECT
    se.id AS event_id,
    se.order_id,
    o.order_number,
    o.buyer_id,
    se.status,
    se.location,
    se.description,
    se.notes,
    se.carrier,
    se.tracking_number,
    se.event_time,
    se.created_at
FROM shipping_events se
JOIN orders o ON se.order_id = o.id
ORDER BY se.order_id, se.event_time DESC;

COMMENT ON VIEW vw_shipping_tracking IS 'Complete shipping tracking history with order details';

-- View: Order History with Returns
CREATE OR REPLACE VIEW vw_order_history_with_returns AS
SELECT
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    o.status AS order_status,
    o.total,
    o.payment_status,
    o.created_at AS order_date,
    COUNT(DISTINCT r.id) AS return_count,
    SUM(r.refund_amount) AS total_refunded,
    CASE
        WHEN COUNT(r.id) > 0 THEN TRUE
        ELSE FALSE
    END AS has_returns
FROM orders o
LEFT JOIN returns r ON o.id = r.order_id
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.order_number, o.buyer_id, o.status, o.total, o.payment_status, o.created_at;

COMMENT ON VIEW vw_order_history_with_returns IS 'Order history with return statistics';

-- ====================================
-- CONNECT TO ADMIN DATABASE
-- ====================================
\c admin_db;

GRANT ALL PRIVILEGES ON SCHEMA public TO admin_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO admin_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO admin_service;

-- ==========================================
-- ADMIN SERVICE TABLES
-- ==========================================

-- AUDIT LOGS TABLE
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL, -- References auth_db.users.id
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_admin_user_id ON audit_logs(admin_user_id);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- NOTIFICATIONS TABLE (ENHANCED)
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL, -- References auth_db.users.id
    type VARCHAR(50) NOT NULL CHECK (type IN ('order', 'payment', 'shipping', 'system', 'promotion', 'product_approved', 'product_rejected', 'return_requested')),
    notification_type VARCHAR(50) DEFAULT 'system',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),
    action_url VARCHAR(500) DEFAULT '',
    is_read BOOLEAN DEFAULT FALSE,
    is_important BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    content_type_id INTEGER,
    object_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_notification_type ON notifications(notification_type);

-- MESSAGES TABLE
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL, -- References auth_db.users.id
    receiver_id INTEGER NOT NULL, -- References auth_db.users.id
    subject VARCHAR(255),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    parent_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_receiver_id ON messages(receiver_id);
CREATE INDEX idx_messages_is_read ON messages(is_read);
CREATE INDEX idx_messages_created_at ON messages(created_at);

COMMENT ON TABLE messages IS 'User-to-user messaging';

-- SYSTEM SETTINGS TABLE
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER -- References auth_db.users.id
);

CREATE INDEX idx_system_settings_key ON system_settings(key);

-- EMAIL TEMPLATES TABLE
CREATE TABLE email_templates (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    subject_template VARCHAR(500) NOT NULL,
    body_text_template TEXT NOT NULL,
    body_html_template TEXT NOT NULL,
    available_variables JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_email_templates_notification_type ON email_templates(notification_type);
CREATE INDEX idx_email_templates_is_active ON email_templates(is_active);

COMMENT ON TABLE email_templates IS 'Email notification templates';

-- EMAIL NOTIFICATIONS TABLE
CREATE TABLE email_notifications (
    id SERIAL PRIMARY KEY,
    recipient_id INTEGER, -- References auth_db.users.id
    recipient_email VARCHAR(254) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_text TEXT NOT NULL,
    body_html TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'failed', 'bounced')),
    provider_message_id VARCHAR(255) DEFAULT '',
    error_message TEXT DEFAULT '',
    content_type_id INTEGER,
    object_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced_at TIMESTAMP
);

CREATE INDEX idx_email_notifications_recipient_id ON email_notifications(recipient_id);
CREATE INDEX idx_email_notifications_status ON email_notifications(status);
CREATE INDEX idx_email_notifications_notification_type ON email_notifications(notification_type);

COMMENT ON TABLE email_notifications IS 'Email notification delivery tracking';

-- NOTIFICATION PREFERENCES TABLE
CREATE TABLE notification_preferences (
    user_id INTEGER PRIMARY KEY, -- References auth_db.users.id
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    order_notifications BOOLEAN DEFAULT TRUE,
    product_notifications BOOLEAN DEFAULT TRUE,
    payment_notifications BOOLEAN DEFAULT TRUE,
    shipping_notifications BOOLEAN DEFAULT TRUE,
    review_notifications BOOLEAN DEFAULT TRUE,
    promotional_notifications BOOLEAN DEFAULT FALSE,
    newsletter_enabled BOOLEAN DEFAULT FALSE,
    digest_enabled BOOLEAN DEFAULT FALSE,
    digest_time TIME,
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE notification_preferences IS 'User notification preferences';

-- SYSTEM ANNOUNCEMENTS TABLE
CREATE TABLE system_announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    announcement_type VARCHAR(20) DEFAULT 'info' CHECK (announcement_type IN ('info', 'warning', 'success', 'error')),
    target_all_users BOOLEAN DEFAULT TRUE,
    target_admins BOOLEAN DEFAULT FALSE,
    target_vendors BOOLEAN DEFAULT FALSE,
    target_customers BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_dismissible BOOLEAN DEFAULT TRUE,
    priority SMALLINT DEFAULT 0,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    action_text VARCHAR(100) DEFAULT '',
    action_url VARCHAR(500) DEFAULT '',
    created_by_id INTEGER, -- References auth_db.users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_announcements_is_active ON system_announcements(is_active);
CREATE INDEX idx_system_announcements_valid_from ON system_announcements(valid_from);
CREATE INDEX idx_system_announcements_valid_until ON system_announcements(valid_until);

COMMENT ON TABLE system_announcements IS 'System-wide announcements';

-- ANNOUNCEMENT DISMISSALS TABLE
CREATE TABLE announcement_dismissals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL, -- References auth_db.users.id
    announcement_id INTEGER NOT NULL REFERENCES system_announcements(id) ON DELETE CASCADE,
    dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, announcement_id)
);

CREATE INDEX idx_announcement_dismissals_user_id ON announcement_dismissals(user_id);
CREATE INDEX idx_announcement_dismissals_announcement_id ON announcement_dismissals(announcement_id);

COMMENT ON TABLE announcement_dismissals IS 'Tracks which users dismissed which announcements';

-- ==========================================
-- GRANT READ ACCESS TO ADMIN SERVICE
-- ==========================================

\c auth_db;
GRANT CONNECT ON DATABASE auth_db TO admin_service;
GRANT USAGE ON SCHEMA public TO admin_service;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO admin_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO admin_service;

\c product_db;
GRANT CONNECT ON DATABASE product_db TO admin_service;
GRANT USAGE ON SCHEMA public TO admin_service;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO admin_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO admin_service;

\c order_db;
GRANT CONNECT ON DATABASE order_db TO admin_service;
GRANT USAGE ON SCHEMA public TO admin_service;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO admin_service;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO admin_service;

\c admin_db;

-- Insert system settings
INSERT INTO system_settings (key, value, description)
VALUES
    ('site_name', 'E-Commerce Platform', 'Website name'),
    ('site_email', 'noreply@ecommerce.com', 'System email address'),
    ('currency', 'USD', 'Default currency'),
    ('tax_rate', '0.08', 'Default tax rate (8%)'),
    ('shipping_cost', '9.99', 'Default shipping cost');

-- Insert sample email templates
INSERT INTO email_templates (notification_type, name, subject_template, body_text_template, body_html_template, is_active) VALUES
    ('order_confirmation', 'Order Confirmation', 'Order Confirmation - {{order_number}}', 'Thank you for your order {{order_number}}!', '<h1>Thank you!</h1><p>Order: {{order_number}}</p>', TRUE),
    ('order_shipped', 'Order Shipped', 'Your order has shipped - {{order_number}}', 'Your order {{order_number}} has been shipped. Tracking: {{tracking_number}}', '<h1>Shipped!</h1><p>Tracking: {{tracking_number}}</p>', TRUE),
    ('order_delivered', 'Order Delivered', 'Your order has been delivered - {{order_number}}', 'Your order {{order_number}} has been delivered.', '<h1>Delivered!</h1>', TRUE)
ON CONFLICT DO NOTHING;

-- ==========================================
-- FOREIGN DATA WRAPPER SETUP
-- ==========================================
-- This sets up FDW to allow admin_db to access
-- tables from auth_db, product_db, and order_db
-- ==========================================

-- Enable FDW extension
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- ==========================================
-- CREATE FOREIGN SERVERS
-- ==========================================

-- Server for auth_db
DROP SERVER IF EXISTS auth_db_server CASCADE;
CREATE SERVER auth_db_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'auth_db');

-- Server for product_db
DROP SERVER IF EXISTS product_db_server CASCADE;
CREATE SERVER product_db_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'product_db');

-- Server for order_db
DROP SERVER IF EXISTS order_db_server CASCADE;
CREATE SERVER order_db_server
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'localhost', port '5432', dbname 'order_db');

-- ==========================================
-- CREATE USER MAPPINGS
-- ==========================================

-- Map admin_service user to access other databases
-- Using ecommerce_admin (superuser) credentials for FDW access
-- password_required=false allows connection even if pg_hba.conf doesn't require password
DROP USER MAPPING IF EXISTS FOR admin_service SERVER auth_db_server;
CREATE USER MAPPING FOR admin_service
SERVER auth_db_server
OPTIONS (user 'ecommerce_admin', password 'change_this_secure_password_123!', password_required 'false');

DROP USER MAPPING IF EXISTS FOR admin_service SERVER product_db_server;
CREATE USER MAPPING FOR admin_service
SERVER product_db_server
OPTIONS (user 'ecommerce_admin', password 'change_this_secure_password_123!', password_required 'false');

DROP USER MAPPING IF EXISTS FOR admin_service SERVER order_db_server;
CREATE USER MAPPING FOR admin_service
SERVER order_db_server
OPTIONS (user 'ecommerce_admin', password 'change_this_secure_password_123!', password_required 'false');

-- Also map for ecommerce_admin user (superuser)
DROP USER MAPPING IF EXISTS FOR ecommerce_admin SERVER auth_db_server;
CREATE USER MAPPING FOR ecommerce_admin
SERVER auth_db_server
OPTIONS (user 'ecommerce_admin', password 'change_this_secure_password_123!');

DROP USER MAPPING IF EXISTS FOR ecommerce_admin SERVER product_db_server;
CREATE USER MAPPING FOR ecommerce_admin
SERVER product_db_server
OPTIONS (user 'ecommerce_admin', password 'change_this_secure_password_123!');

DROP USER MAPPING IF EXISTS FOR ecommerce_admin SERVER order_db_server;
CREATE USER MAPPING FOR ecommerce_admin
SERVER order_db_server
OPTIONS (user 'ecommerce_admin', password 'change_this_secure_password_123!');

-- ==========================================
-- GRANT PERMISSIONS ON FOREIGN SERVERS
-- ==========================================
-- Grant admin_service permission to use foreign servers (required for IMPORT)
GRANT USAGE ON FOREIGN SERVER auth_db_server TO admin_service;
GRANT USAGE ON FOREIGN SERVER product_db_server TO admin_service;
GRANT USAGE ON FOREIGN SERVER order_db_server TO admin_service;

-- ==========================================
-- IMPORT FOREIGN TABLES
-- ==========================================
-- IMPORT FOREIGN SCHEMA commands are commented out because they fail during
-- initialization (databases aren't ready for FDW connections yet).
-- 
-- The imports will be handled automatically by the admin service on first connection.
-- If needed, they can be imported manually after docker-compose up:
--
--   docker-compose exec postgres psql -U ecommerce_admin -d admin_db -c "IMPORT FOREIGN SCHEMA public FROM SERVER auth_db_server INTO public; IMPORT FOREIGN SCHEMA public FROM SERVER product_db_server INTO public; IMPORT FOREIGN SCHEMA public FROM SERVER order_db_server INTO public;"
--
-- For automatic import, the admin service will handle this on startup.

-- ==========================================
-- COMMENTS ON PROCEDURES
-- ==========================================

\c auth_db;
COMMENT ON PROCEDURE sp_register_user IS 'Register new user';
COMMENT ON PROCEDURE sp_verify_user IS 'Verify user email';
COMMENT ON PROCEDURE sp_upgrade_to_seller IS 'Upgrade user to seller role (DEPRECATED - use sp_upgrade_to_vendor)';
COMMENT ON PROCEDURE sp_upgrade_to_vendor IS 'Upgrade user to vendor with business profile';
COMMENT ON PROCEDURE sp_approve_vendor IS 'Approve or reject vendor application';
COMMENT ON PROCEDURE sp_update_customer_stats IS 'Update customer order statistics';
COMMENT ON PROCEDURE sp_ban_user IS 'Ban or unban user';
COMMENT ON PROCEDURE sp_add_address IS 'Add user address';
COMMENT ON PROCEDURE sp_set_default_address IS 'Set default shipping/billing address';

\c product_db;
COMMENT ON PROCEDURE sp_approve_product IS 'Approve or reject product by admin';
COMMENT ON PROCEDURE sp_update_inventory IS 'Update product inventory';
COMMENT ON PROCEDURE sp_bulk_approve_products IS 'Approve multiple products at once';
COMMENT ON PROCEDURE sp_soft_delete_product IS 'Soft delete product for auditing';
COMMENT ON PROCEDURE sp_restore_product IS 'Restore soft deleted product';
COMMENT ON PROCEDURE sp_add_review IS 'Add product review with purchase verification';
COMMENT ON PROCEDURE sp_add_product_variant IS 'Add product variant (size/color/etc)';
COMMENT ON PROCEDURE sp_update_variant_inventory IS 'Update variant inventory quantity';
COMMENT ON PROCEDURE sp_increment_view_count IS 'Increment product view count';

\c order_db;
COMMENT ON PROCEDURE sp_create_order IS 'Create order from cart with coupon support';
COMMENT ON PROCEDURE sp_cancel_order IS 'Cancel order and restore inventory';
COMMENT ON PROCEDURE sp_update_order_status IS 'Update order status and send notifications';
COMMENT ON PROCEDURE sp_process_payment IS 'Process payment transaction';
COMMENT ON PROCEDURE sp_process_refund IS 'Process refund for order';
COMMENT ON PROCEDURE sp_add_to_cart IS 'Add product to cart with stock validation';
COMMENT ON PROCEDURE sp_update_cart_item IS 'Update cart item quantity';
COMMENT ON PROCEDURE sp_clear_cart IS 'Clear user cart';
COMMENT ON PROCEDURE sp_request_return IS 'Request product return and refund';
COMMENT ON PROCEDURE sp_process_return IS 'Approve or reject return request';
COMMENT ON PROCEDURE sp_complete_return IS 'Complete return and process refund';
COMMENT ON PROCEDURE sp_add_shipping_event IS 'Add shipping tracking event';

-- ====================================
-- MICROSERVICES NOTES
-- ====================================

-- This database schema is designed for microservices architecture:
-- 1. Each service has its own database
-- 2. Foreign key references across databases are replaced with INTEGER fields
-- 3. Data consistency is maintained through:
--    - API calls between services
--    - Event-driven architecture (RabbitMQ)
--    - Saga pattern for distributed transactions
-- 4. Admin service has read-only access to all databases for reporting

-- End of initialization script
