-- E-Commerce Database Schema
-- Created: 2025
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================
-- USERS TABLE
-- ====================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'seller', 'admin')),
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ====================================
-- CATEGORIES TABLE
-- ====================================
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    description TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_is_active ON categories(is_active);

-- ====================================
-- PRODUCTS TABLE
-- ====================================
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    compare_at_price DECIMAL(10, 2) CHECK (compare_at_price >= 0),
    cost_per_item DECIMAL(10, 2) CHECK (cost_per_item >= 0),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    sku VARCHAR(100),
    barcode VARCHAR(100),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    brand VARCHAR(100),
    condition VARCHAR(20) CHECK (condition IN ('new', 'used', 'refurbished')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'rejected', 'archived')),
    approval_status VARCHAR(20) DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    weight DECIMAL(10, 2),
    dimensions_length DECIMAL(10, 2),
    dimensions_width DECIMAL(10, 2),
    dimensions_height DECIMAL(10, 2),
    views_count INTEGER DEFAULT 0,
    favorites_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_seller_id ON products(seller_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_approval_status ON products(approval_status);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_created_at ON products(created_at);
CREATE INDEX idx_products_title ON products USING gin(to_tsvector('english', title));

-- ====================================
-- PRODUCT IMAGES TABLE
-- ====================================
CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    position INTEGER DEFAULT 0,
    alt_text VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_images_product_id ON product_images(product_id);

-- ====================================
-- ADDRESSES TABLE
-- ====================================
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) CHECK (type IN ('shipping', 'billing')),
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_addresses_type ON addresses(type);

-- ====================================
-- ORDERS TABLE
-- ====================================
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    buyer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')),
    subtotal DECIMAL(10, 2) NOT NULL,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    tax DECIMAL(10, 2) DEFAULT 0,
    discount DECIMAL(10, 2) DEFAULT 0,
    total DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    payment_method VARCHAR(50),
    shipping_address_id INTEGER REFERENCES addresses(id) ON DELETE SET NULL,
    billing_address_id INTEGER REFERENCES addresses(id) ON DELETE SET NULL,
    tracking_number VARCHAR(100),
    carrier VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ====================================
-- ORDER ITEMS TABLE
-- ====================================
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    seller_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_seller_id ON order_items(seller_id);

-- ====================================
-- PAYMENTS TABLE
-- ====================================
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    stripe_payment_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
    payment_method VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_stripe_payment_id ON payments(stripe_payment_id);
CREATE INDEX idx_payments_status ON payments(status);

-- ====================================
-- REVIEWS TABLE
-- ====================================
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, user_id, order_id)
);

CREATE INDEX idx_reviews_product_id ON reviews(product_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_created_at ON reviews(created_at);

-- ====================================
-- SHOPPING CART TABLE
-- ====================================
CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_cart_items_user_id ON cart_items(user_id);
CREATE INDEX idx_cart_items_product_id ON cart_items(product_id);

-- ====================================
-- WISHLIST TABLE
-- ====================================
CREATE TABLE wishlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, product_id)
);

CREATE INDEX idx_wishlist_user_id ON wishlist(user_id);
CREATE INDEX idx_wishlist_product_id ON wishlist(product_id);

-- ====================================
-- MESSAGES TABLE
-- ====================================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
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

-- ====================================
-- COUPONS TABLE
-- ====================================
CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(20) CHECK (type IN ('percentage', 'fixed')),
    value DECIMAL(10, 2) NOT NULL,
    min_purchase_amount DECIMAL(10, 2),
    max_discount_amount DECIMAL(10, 2),
    usage_limit INTEGER,
    used_count INTEGER DEFAULT 0,
    starts_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coupons_code ON coupons(code);
CREATE INDEX idx_coupons_is_active ON coupons(is_active);
CREATE INDEX idx_coupons_expires_at ON coupons(expires_at);

-- ====================================
-- NOTIFICATIONS TABLE
-- ====================================
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    link TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- ====================================
-- PRODUCT VARIANTS TABLE (NEW)
-- ====================================
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
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
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE product_variants IS 'Product variations (size, color, material)';

CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_product_variants_is_active ON product_variants(is_active);

-- ====================================
-- RETURNS TABLE (NEW)
-- ====================================
CREATE TABLE returns (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    order_item_id INTEGER REFERENCES order_items(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'requested' CHECK (status IN ('requested', 'approved', 'rejected', 'processing', 'completed', 'cancelled')),
    refund_amount DECIMAL(10, 2) NOT NULL CHECK (refund_amount >= 0),
    refund_method VARCHAR(50),
    return_tracking_number VARCHAR(100),
    admin_notes TEXT,
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE returns IS 'Product return and refund tracking';

CREATE INDEX idx_returns_order_id ON returns(order_id);
CREATE INDEX idx_returns_user_id ON returns(user_id);
CREATE INDEX idx_returns_status ON returns(status);
CREATE INDEX idx_returns_created_at ON returns(created_at);

-- ====================================
-- SHIPPING EVENTS TABLE (NEW)
-- ====================================
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

-- ====================================
-- TRIGGERS FOR UPDATED_AT
-- ====================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_variants_updated_at BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_returns_updated_at BEFORE UPDATE ON returns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ====================================
-- ENHANCEMENTS: ADD COLUMNS TO EXISTING TABLES
-- ====================================

-- Add soft delete columns for auditing
ALTER TABLE products ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;
ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

-- Add coupon tracking to orders
ALTER TABLE orders ADD COLUMN coupon_id INTEGER REFERENCES coupons(id) ON DELETE SET NULL;

-- Create indexes for new columns
CREATE INDEX idx_products_deleted_at ON products(deleted_at);
CREATE INDEX idx_orders_deleted_at ON orders(deleted_at);
CREATE INDEX idx_orders_coupon_id ON orders(coupon_id);

-- Add comments
COMMENT ON COLUMN products.deleted_at IS 'Soft delete timestamp for auditing';
COMMENT ON COLUMN orders.deleted_at IS 'Soft delete timestamp for auditing';
COMMENT ON COLUMN orders.coupon_id IS 'Coupon used for this order';

-- ====================================
-- SAMPLE DATA (OPTIONAL)
-- ====================================

-- Insert admin user
INSERT INTO users (email, password_hash, first_name, last_name, role, is_verified, is_active)
VALUES ('admin@ecommerce.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr.G.qO8G', 'Admin', 'User', 'admin', TRUE, TRUE);

-- Insert sample categories
INSERT INTO categories (name, slug, description, is_active, position)
VALUES 
    ('Electronics', 'electronics', 'Electronic devices and gadgets', TRUE, 1),
    ('Fashion', 'fashion', 'Clothing and accessories', TRUE, 2),
    ('Home & Garden', 'home-garden', 'Home and garden products', TRUE, 3),
    ('Sports', 'sports', 'Sports and outdoor equipment', TRUE, 4),
    ('Books', 'books', 'Books and magazines', TRUE, 5);

-- Insert subcategories
INSERT INTO categories (name, slug, parent_id, description, is_active, position)
VALUES 
    ('Smartphones', 'smartphones', 1, 'Mobile phones and accessories', TRUE, 1),
    ('Laptops', 'laptops', 1, 'Laptop computers', TRUE, 2),
    ('Men Fashion', 'men-fashion', 2, 'Men clothing and accessories', TRUE, 1),
    ('Women Fashion', 'women-fashion', 2, 'Women clothing and accessories', TRUE, 2);

-- ====================================
-- VIEWS FOR COMMON QUERIES
-- ====================================

-- View: Products with category names
CREATE OR REPLACE VIEW vw_products_with_categories AS
SELECT 
    p.*,
    c.name AS category_name,
    c.slug AS category_slug,
    u.first_name || ' ' || u.last_name AS seller_name,
    u.email AS seller_email,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(r.id) AS review_count
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN users u ON p.seller_id = u.id
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, c.name, c.slug, u.first_name, u.last_name, u.email;

-- View: Order details with items
CREATE OR REPLACE VIEW vw_order_details AS
SELECT 
    o.*,
    u.email AS buyer_email,
    u.first_name || ' ' || u.last_name AS buyer_name,
    sa.address_line1 AS shipping_address,
    sa.city AS shipping_city,
    sa.country AS shipping_country
FROM orders o
LEFT JOIN users u ON o.buyer_id = u.id
LEFT JOIN addresses sa ON o.shipping_address_id = sa.id;

-- View: User statistics
CREATE OR REPLACE VIEW vw_user_statistics AS
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    COUNT(DISTINCT CASE WHEN u.role = 'seller' THEN p.id END) AS products_count,
    COUNT(DISTINCT o.id) AS orders_count,
    COALESCE(SUM(o.total), 0) AS total_spent,
    COUNT(DISTINCT r.id) AS reviews_count
FROM users u
LEFT JOIN products p ON u.id = p.seller_id
LEFT JOIN orders o ON u.id = o.buyer_id
LEFT JOIN reviews r ON u.id = r.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name, u.role;

-- ==========================================
-- SHOPPING & CART VIEWS
-- ==========================================

-- View: Cart details with product information
CREATE OR REPLACE VIEW vw_cart_details AS
SELECT 
    c.id AS cart_item_id,
    c.user_id,
    c.product_id,
    c.quantity,
    c.created_at,
    c.updated_at,
    p.title AS product_title,
    p.description AS product_description,
    p.price AS product_price,
    p.quantity AS available_quantity,
    p.seller_id,
    u.first_name || ' ' || u.last_name AS seller_name,
    cat.name AS category_name,
    pi.image_url AS product_image,
    (c.quantity * p.price) AS item_subtotal,
    CASE 
        WHEN p.quantity >= c.quantity THEN TRUE 
        ELSE FALSE 
    END AS in_stock
FROM cart_items c
JOIN products p ON c.product_id = p.id
JOIN users u ON p.seller_id = u.id
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN LATERAL (
    SELECT image_url 
    FROM product_images 
    WHERE product_id = p.id 
    ORDER BY position 
    LIMIT 1
) pi ON TRUE;

-- View: Cart summary by user
CREATE OR REPLACE VIEW vw_cart_summary AS
SELECT 
    user_id,
    COUNT(DISTINCT product_id) AS total_items,
    SUM(quantity) AS total_quantity,
    SUM(item_subtotal) AS cart_subtotal,
    BOOL_AND(in_stock) AS all_in_stock
FROM vw_cart_details
GROUP BY user_id;

-- View: Wishlist with product details
CREATE OR REPLACE VIEW vw_wishlist_details AS
SELECT 
    w.id AS wishlist_id,
    w.user_id,
    w.product_id,
    w.created_at,
    p.title AS product_title,
    p.description AS product_description,
    p.price AS product_price,
    p.compare_at_price,
    p.quantity AS available_quantity,
    p.status,
    p.approval_status,
    p.seller_id,
    u.first_name || ' ' || u.last_name AS seller_name,
    cat.name AS category_name,
    pi.image_url AS product_image,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(r.id) AS review_count,
    CASE 
        WHEN p.quantity > 0 AND p.approval_status = 'approved' THEN TRUE 
        ELSE FALSE 
    END AS available
FROM wishlist w
JOIN products p ON w.product_id = p.id
JOIN users u ON p.seller_id = u.id
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN reviews r ON p.id = r.product_id
LEFT JOIN LATERAL (
    SELECT image_url 
    FROM product_images 
    WHERE product_id = p.id 
    ORDER BY position 
    LIMIT 1
) pi ON TRUE
GROUP BY w.id, w.user_id, w.product_id, w.created_at, p.title, p.description, 
         p.price, p.compare_at_price, p.quantity, p.status, p.approval_status,
         p.seller_id, u.first_name, u.last_name, cat.name, pi.image_url;

-- View: Product inventory status
CREATE OR REPLACE VIEW vw_product_inventory_status AS
SELECT 
    p.id AS product_id,
    p.title,
    p.sku,
    p.quantity AS current_stock,
    p.seller_id,
    u.first_name || ' ' || u.last_name AS seller_name,
    u.email AS seller_email,
    cat.name AS category_name,
    CASE 
        WHEN p.quantity = 0 THEN 'OUT_OF_STOCK'
        WHEN p.quantity <= 5 THEN 'LOW_STOCK'
        WHEN p.quantity <= 20 THEN 'MEDIUM_STOCK'
        ELSE 'IN_STOCK'
    END AS stock_status,
    COALESCE(SUM(ci.quantity), 0) AS reserved_in_carts,
    (p.quantity - COALESCE(SUM(ci.quantity), 0)) AS available_quantity
FROM products p
JOIN users u ON p.seller_id = u.id
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN cart_items ci ON p.id = ci.product_id
WHERE p.approval_status = 'approved'
GROUP BY p.id, p.title, p.sku, p.quantity, p.seller_id, 
         u.first_name, u.last_name, u.email, cat.name;

-- ==========================================
-- ORDER MANAGEMENT VIEWS
-- ==========================================

-- View: Order items with full details
CREATE OR REPLACE VIEW vw_order_items_full AS
SELECT 
    oi.id AS order_item_id,
    oi.order_id,
    oi.product_id,
    oi.seller_id,
    oi.title AS product_title,
    oi.quantity,
    oi.price AS unit_price,
    oi.total AS item_total,
    oi.created_at,
    o.order_number,
    o.buyer_id,
    o.status AS order_status,
    o.payment_status,
    buyer.first_name || ' ' || buyer.last_name AS buyer_name,
    buyer.email AS buyer_email,
    seller.first_name || ' ' || seller.last_name AS seller_name,
    seller.email AS seller_email,
    p.sku,
    pi.image_url AS product_image
FROM order_items oi
JOIN orders o ON oi.order_id = o.id
JOIN users buyer ON o.buyer_id = buyer.id
JOIN users seller ON oi.seller_id = seller.id
LEFT JOIN products p ON oi.product_id = p.id
LEFT JOIN LATERAL (
    SELECT image_url 
    FROM product_images 
    WHERE product_id = p.id 
    ORDER BY position 
    LIMIT 1
) pi ON TRUE;

-- View: Complete order history
CREATE OR REPLACE VIEW vw_order_history_complete AS
SELECT 
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    buyer.first_name || ' ' || buyer.last_name AS buyer_name,
    buyer.email AS buyer_email,
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
    sa.address_line1 AS shipping_address,
    sa.city AS shipping_city,
    sa.postal_code AS shipping_postal_code,
    sa.country AS shipping_country,
    ba.address_line1 AS billing_address,
    ba.city AS billing_city,
    p.status AS payment_record_status,
    p.stripe_payment_id
FROM orders o
JOIN users buyer ON o.buyer_id = buyer.id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN addresses sa ON o.shipping_address_id = sa.id
LEFT JOIN addresses ba ON o.billing_address_id = ba.id
LEFT JOIN payments p ON o.id = p.order_id
GROUP BY o.id, o.order_number, o.buyer_id, buyer.first_name, buyer.last_name,
         buyer.email, o.status, o.payment_status, o.payment_method, o.subtotal,
         o.shipping_cost, o.tax, o.discount, o.total, o.tracking_number, o.carrier,
         o.created_at, o.updated_at, sa.address_line1, sa.city, sa.postal_code,
         sa.country, ba.address_line1, ba.city, p.status, p.stripe_payment_id;

-- View: Pending orders (need action)
CREATE OR REPLACE VIEW vw_pending_orders AS
SELECT 
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    buyer.first_name || ' ' || buyer.last_name AS buyer_name,
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
    COUNT(DISTINCT oi.seller_id) AS seller_count,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - o.created_at))/3600 AS hours_since_order
FROM orders o
JOIN users buyer ON o.buyer_id = buyer.id
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.status IN ('pending', 'confirmed', 'processing')
GROUP BY o.id, o.order_number, o.buyer_id, buyer.first_name, buyer.last_name,
         o.status, o.payment_status, o.total, o.created_at;

-- View: Order shipping information (basic)
DROP VIEW IF EXISTS vw_shipping_tracking CASCADE;
CREATE OR REPLACE VIEW vw_order_shipping_info AS
SELECT 
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    buyer.first_name || ' ' || buyer.last_name AS buyer_name,
    buyer.email AS buyer_email,
    buyer.phone AS buyer_phone,
    o.status AS order_status,
    o.tracking_number,
    o.carrier,
    o.created_at AS order_date,
    o.updated_at AS last_update,
    sa.first_name || ' ' || sa.last_name AS recipient_name,
    sa.address_line1,
    sa.address_line2,
    sa.city,
    sa.state,
    sa.postal_code,
    sa.country,
    sa.phone AS delivery_phone,
    CASE 
        WHEN o.status = 'pending' THEN 1
        WHEN o.status = 'confirmed' THEN 2
        WHEN o.status = 'processing' THEN 3
        WHEN o.status = 'shipped' THEN 4
        WHEN o.status = 'delivered' THEN 5
        ELSE 0
    END AS status_stage
FROM orders o
JOIN users buyer ON o.buyer_id = buyer.id
LEFT JOIN addresses sa ON o.shipping_address_id = sa.id
WHERE o.status NOT IN ('cancelled', 'refunded');

-- ==========================================
-- SELLER & ADMIN VIEWS
-- ==========================================

-- View: Seller products performance
CREATE OR REPLACE VIEW vw_seller_products_performance AS
SELECT 
    p.id AS product_id,
    p.seller_id,
    seller.first_name || ' ' || seller.last_name AS seller_name,
    p.title,
    p.price,
    p.quantity AS current_stock,
    p.status,
    p.approval_status,
    p.views_count,
    p.favorites_count,
    p.created_at,
    cat.name AS category_name,
    COUNT(DISTINCT oi.id) AS total_sales,
    SUM(oi.quantity) AS units_sold,
    COALESCE(SUM(oi.total), 0) AS total_revenue,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(DISTINCT r.id) AS review_count,
    pi.image_url AS product_image
FROM products p
JOIN users seller ON p.seller_id = seller.id
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN reviews r ON p.id = r.product_id
LEFT JOIN LATERAL (
    SELECT image_url 
    FROM product_images 
    WHERE product_id = p.id 
    ORDER BY position 
    LIMIT 1
) pi ON TRUE
GROUP BY p.id, p.seller_id, seller.first_name, seller.last_name, p.title,
         p.price, p.quantity, p.status, p.approval_status, p.views_count,
         p.favorites_count, p.created_at, cat.name, pi.image_url;

-- View: Pending product approvals
CREATE OR REPLACE VIEW vw_pending_approvals AS
SELECT 
    p.id AS product_id,
    p.title,
    p.description,
    p.price,
    p.quantity,
    p.seller_id,
    seller.first_name || ' ' || seller.last_name AS seller_name,
    seller.email AS seller_email,
    p.category_id,
    cat.name AS category_name,
    p.created_at AS submitted_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - p.created_at))/3600 AS hours_pending,
    pi.image_url AS product_image,
    COUNT(DISTINCT pi2.id) AS total_images
FROM products p
JOIN users seller ON p.seller_id = seller.id
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN LATERAL (
    SELECT image_url 
    FROM product_images 
    WHERE product_id = p.id 
    ORDER BY position 
    LIMIT 1
) pi ON TRUE
LEFT JOIN product_images pi2 ON p.id = pi2.product_id
WHERE p.approval_status = 'pending'
GROUP BY p.id, p.title, p.description, p.price, p.quantity, p.seller_id,
         seller.first_name, seller.last_name, seller.email, p.category_id,
         cat.name, p.created_at, pi.image_url
ORDER BY p.created_at ASC;

-- View: Seller revenue breakdown
CREATE OR REPLACE VIEW vw_seller_revenue AS
SELECT 
    seller.id AS seller_id,
    seller.first_name || ' ' || seller.last_name AS seller_name,
    seller.email AS seller_email,
    COUNT(DISTINCT p.id) AS total_products,
    COUNT(DISTINCT CASE WHEN p.approval_status = 'approved' THEN p.id END) AS approved_products,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS total_units_sold,
    COALESCE(SUM(oi.total), 0) AS gross_revenue,
    COALESCE(SUM(oi.total * 0.10), 0) AS platform_commission,
    COALESCE(SUM(oi.total * 0.90), 0) AS net_revenue,
    AVG(oi.price) AS avg_item_price,
    COALESCE(AVG(r.rating), 0) AS avg_seller_rating,
    COUNT(DISTINCT r.id) AS total_reviews
FROM users seller
LEFT JOIN products p ON seller.id = p.seller_id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id AND o.payment_status = 'paid'
LEFT JOIN reviews r ON p.id = r.product_id
WHERE seller.role = 'seller'
GROUP BY seller.id, seller.first_name, seller.last_name, seller.email;

-- View: Seller dashboard summary
CREATE OR REPLACE VIEW vw_seller_dashboard_summary AS
SELECT 
    s.seller_id,
    s.seller_name,
    s.total_products,
    s.approved_products,
    s.total_orders,
    s.gross_revenue,
    s.net_revenue,
    s.avg_seller_rating,
    pending.pending_products,
    recent.recent_orders_count,
    recent.recent_revenue,
    stock.low_stock_count,
    stock.out_of_stock_count
FROM vw_seller_revenue s
LEFT JOIN (
    SELECT seller_id, COUNT(*) AS pending_products
    FROM products
    WHERE approval_status = 'pending'
    GROUP BY seller_id
) pending ON s.seller_id = pending.seller_id
LEFT JOIN (
    SELECT oi.seller_id, 
           COUNT(DISTINCT o.id) AS recent_orders_count,
           SUM(oi.total) AS recent_revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE o.created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
    AND o.payment_status = 'paid'
    GROUP BY oi.seller_id
) recent ON s.seller_id = recent.seller_id
LEFT JOIN (
    SELECT seller_id,
           COUNT(*) FILTER (WHERE quantity > 0 AND quantity <= 5) AS low_stock_count,
           COUNT(*) FILTER (WHERE quantity = 0) AS out_of_stock_count
    FROM products
    WHERE approval_status = 'approved'
    GROUP BY seller_id
) stock ON s.seller_id = stock.seller_id;

-- ==========================================
-- ANALYTICS & REVIEWS VIEWS
-- ==========================================

-- View: Product reviews with details
CREATE OR REPLACE VIEW vw_product_reviews_detailed AS
SELECT 
    r.id AS review_id,
    r.product_id,
    p.title AS product_title,
    p.seller_id,
    seller.first_name || ' ' || seller.last_name AS seller_name,
    r.user_id,
    reviewer.first_name || ' ' || reviewer.last_name AS reviewer_name,
    reviewer.avatar_url AS reviewer_avatar,
    r.order_id,
    r.rating,
    r.title AS review_title,
    r.comment,
    r.is_verified_purchase,
    r.helpful_count,
    r.created_at,
    r.updated_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.created_at))/86400 AS days_ago
FROM reviews r
JOIN products p ON r.product_id = p.id
JOIN users seller ON p.seller_id = seller.id
JOIN users reviewer ON r.user_id = reviewer.id
ORDER BY r.created_at DESC;

-- View: Popular products
CREATE OR REPLACE VIEW vw_popular_products AS
SELECT 
    p.id AS product_id,
    p.title,
    p.description,
    p.price,
    p.compare_at_price,
    p.seller_id,
    seller.first_name || ' ' || seller.last_name AS seller_name,
    cat.name AS category_name,
    p.views_count,
    p.favorites_count,
    COUNT(DISTINCT oi.id) AS sales_count,
    SUM(oi.quantity) AS units_sold,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(DISTINCT r.id) AS review_count,
    pi.image_url AS product_image,
    (p.views_count * 0.3 + p.favorites_count * 0.5 + COUNT(DISTINCT oi.id) * 2) AS popularity_score
FROM products p
JOIN users seller ON p.seller_id = seller.id
LEFT JOIN categories cat ON p.category_id = cat.id
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN reviews r ON p.id = r.product_id
LEFT JOIN LATERAL (
    SELECT image_url 
    FROM product_images 
    WHERE product_id = p.id 
    ORDER BY position 
    LIMIT 1
) pi ON TRUE
WHERE p.approval_status = 'approved'
AND p.quantity > 0
GROUP BY p.id, p.title, p.description, p.price, p.compare_at_price, p.seller_id,
         seller.first_name, seller.last_name, cat.name, p.views_count,
         p.favorites_count, pi.image_url
ORDER BY popularity_score DESC;

-- View: Recent activity feed
CREATE OR REPLACE VIEW vw_recent_activity AS
SELECT 
    'ORDER' AS activity_type,
    o.id AS reference_id,
    o.buyer_id AS user_id,
    buyer.first_name || ' ' || buyer.last_name AS user_name,
    'Order ' || o.order_number || ' placed' AS activity_description,
    o.total AS amount,
    o.created_at AS activity_time
FROM orders o
JOIN users buyer ON o.buyer_id = buyer.id

UNION ALL

SELECT 
    'REVIEW' AS activity_type,
    r.id AS reference_id,
    r.user_id,
    reviewer.first_name || ' ' || reviewer.last_name AS user_name,
    'Reviewed "' || p.title || '" - ' || r.rating || ' stars' AS activity_description,
    NULL AS amount,
    r.created_at AS activity_time
FROM reviews r
JOIN users reviewer ON r.user_id = reviewer.id
JOIN products p ON r.product_id = p.id

UNION ALL

SELECT 
    'PRODUCT' AS activity_type,
    p.id AS reference_id,
    p.seller_id AS user_id,
    seller.first_name || ' ' || seller.last_name AS user_name,
    'Listed new product: ' || p.title AS activity_description,
    p.price AS amount,
    p.created_at AS activity_time
FROM products p
JOIN users seller ON p.seller_id = seller.id
WHERE p.approval_status = 'approved'

UNION ALL

SELECT 
    'USER' AS activity_type,
    u.id AS reference_id,
    u.id AS user_id,
    u.first_name || ' ' || u.last_name AS user_name,
    'New user registered' AS activity_description,
    NULL AS amount,
    u.created_at AS activity_time
FROM users u

ORDER BY activity_time DESC
LIMIT 100;

-- ====================================
-- NEW VIEWS FOR ENHANCED FEATURES
-- ====================================

-- View: Active Products (excluding soft deleted)
CREATE OR REPLACE VIEW vw_active_products AS
SELECT 
    p.*,
    c.name AS category_name,
    u.first_name || ' ' || u.last_name AS seller_name,
    COALESCE(AVG(r.rating), 0) AS avg_rating,
    COUNT(r.id) AS review_count
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN users u ON p.seller_id = u.id
LEFT JOIN reviews r ON p.id = r.product_id
WHERE p.deleted_at IS NULL
GROUP BY p.id, c.name, u.first_name, u.last_name;

COMMENT ON VIEW vw_active_products IS 'Products that are not soft deleted';

-- View: Product Variants with Details
CREATE OR REPLACE VIEW vw_product_variants_details AS
SELECT 
    pv.*,
    p.title AS product_title,
    p.seller_id,
    u.first_name || ' ' || u.last_name AS seller_name,
    p.category_id,
    c.name AS category_name,
    CASE 
        WHEN pv.quantity > 0 AND pv.is_active = TRUE THEN TRUE
        ELSE FALSE
    END AS available
FROM product_variants pv
JOIN products p ON pv.product_id = p.id
LEFT JOIN users u ON p.seller_id = u.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.deleted_at IS NULL;

COMMENT ON VIEW vw_product_variants_details IS 'Product variants with product and seller details';

-- View: Returns with Details
CREATE OR REPLACE VIEW vw_returns_details AS
SELECT 
    r.id AS return_id,
    r.order_id,
    o.order_number,
    r.user_id,
    u.email AS user_email,
    u.first_name || ' ' || u.last_name AS user_name,
    r.reason,
    r.status,
    r.refund_amount,
    r.refund_method,
    r.return_tracking_number,
    r.admin_notes,
    approver.first_name || ' ' || approver.last_name AS approved_by_name,
    r.approved_at,
    r.completed_at,
    r.created_at,
    r.updated_at,
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - r.created_at)) AS days_pending
FROM returns r
LEFT JOIN orders o ON r.order_id = o.id
LEFT JOIN users u ON r.user_id = u.id
LEFT JOIN users approver ON r.approved_by = approver.id;

COMMENT ON VIEW vw_returns_details IS 'Returns with order, user, and approval details';

-- View: Shipping Tracking History
CREATE OR REPLACE VIEW vw_shipping_tracking AS
SELECT 
    se.id AS event_id,
    se.order_id,
    o.order_number,
    o.buyer_id,
    u.email AS buyer_email,
    u.first_name || ' ' || u.last_name AS buyer_name,
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
LEFT JOIN users u ON o.buyer_id = u.id
ORDER BY se.order_id, se.event_time DESC;

COMMENT ON VIEW vw_shipping_tracking IS 'Complete shipping tracking history with order details';

-- View: Order History with Returns
CREATE OR REPLACE VIEW vw_order_history_with_returns AS
SELECT 
    o.id AS order_id,
    o.order_number,
    o.buyer_id,
    buyer.email AS buyer_email,
    buyer.first_name || ' ' || buyer.last_name AS buyer_name,
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
LEFT JOIN users buyer ON o.buyer_id = buyer.id
LEFT JOIN returns r ON o.id = r.order_id
WHERE o.deleted_at IS NULL
GROUP BY o.id, o.order_number, o.buyer_id, buyer.email, buyer.first_name, 
         buyer.last_name, o.status, o.total, o.payment_status, o.created_at;

COMMENT ON VIEW vw_order_history_with_returns IS 'Order history with return statistics';

-- ====================================
-- DATABASE INFORMATION
-- ====================================
COMMENT ON DATABASE ecommerce_db IS 'E-Commerce Multi-Vendor Marketplace Database';
COMMENT ON TABLE users IS 'User accounts (buyers, sellers, admins)';
COMMENT ON TABLE products IS 'Product listings from sellers';
COMMENT ON TABLE orders IS 'Customer orders';
COMMENT ON TABLE order_items IS 'Individual items in orders';
COMMENT ON TABLE payments IS 'Payment transactions';
COMMENT ON TABLE reviews IS 'Product reviews and ratings';
COMMENT ON TABLE categories IS 'Product categories (hierarchical)';
COMMENT ON TABLE addresses IS 'User shipping and billing addresses';
COMMENT ON TABLE cart_items IS 'Shopping cart items';
COMMENT ON TABLE wishlist IS 'User wishlists';
COMMENT ON TABLE messages IS 'User-to-user messaging';
COMMENT ON TABLE coupons IS 'Discount coupons';
COMMENT ON TABLE notifications IS 'User notifications';

-- Views documentation
COMMENT ON VIEW vw_products_with_categories IS 'Products with category and seller information, includes average rating';
COMMENT ON VIEW vw_order_details IS 'Orders with buyer information and shipping address';
COMMENT ON VIEW vw_user_statistics IS 'User statistics including products, orders, and reviews count';
COMMENT ON VIEW vw_cart_details IS 'Shopping cart with product details, prices, and availability';
COMMENT ON VIEW vw_cart_summary IS 'Cart summary by user with totals and stock status';
COMMENT ON VIEW vw_wishlist_details IS 'Wishlist with complete product information and ratings';
COMMENT ON VIEW vw_product_inventory_status IS 'Product stock levels with low stock alerts';
COMMENT ON VIEW vw_order_items_full IS 'Order items with complete buyer, seller, and product details';
COMMENT ON VIEW vw_order_history_complete IS 'Complete order history with addresses and payment info';
COMMENT ON VIEW vw_pending_orders IS 'Orders requiring action with priority indicators';
COMMENT ON VIEW vw_shipping_tracking IS 'Shipping tracking information with delivery addresses';
COMMENT ON VIEW vw_seller_products_performance IS 'Seller products with sales performance metrics';
COMMENT ON VIEW vw_pending_approvals IS 'Products awaiting admin approval with submission time';
COMMENT ON VIEW vw_seller_revenue IS 'Seller revenue breakdown with commission calculations';
COMMENT ON VIEW vw_seller_dashboard_summary IS 'Comprehensive seller dashboard with key metrics';
COMMENT ON VIEW vw_product_reviews_detailed IS 'Product reviews with reviewer and product information';
COMMENT ON VIEW vw_popular_products IS 'Popular products ranked by views, favorites, and sales';
COMMENT ON VIEW vw_recent_activity IS 'Recent platform activity feed (orders, reviews, new products)';

-- ====================================
-- STORED PROCEDURES
-- ====================================

-- ==========================================
-- 1. ORDER MANAGEMENT PROCEDURES
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
    v_shipping_cost DECIMAL(10, 2) := 0;
    v_tax DECIMAL(10, 2) := 0;
    v_discount DECIMAL(10, 2) := 0;
    v_cart_item RECORD;
    v_coupon RECORD;
BEGIN
    -- Calculate subtotal from cart
    SELECT SUM(p.price * c.quantity) INTO v_subtotal
    FROM cart_items c
    JOIN products p ON c.product_id = p.id
    WHERE c.user_id = p_buyer_id;
    
    IF v_subtotal IS NULL OR v_subtotal = 0 THEN
        RAISE EXCEPTION 'Cart is empty';
    END IF;
    
    -- Calculate shipping (example: flat rate)
    v_shipping_cost := 10.00;
    
    -- Calculate tax (example: 10%)
    v_tax := v_subtotal * 0.10;
    
    -- Apply coupon if provided
    IF p_coupon_code IS NOT NULL THEN
        SELECT * INTO v_coupon FROM coupons 
        WHERE code = p_coupon_code 
        AND is_active = TRUE
        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        AND (usage_limit IS NULL OR used_count < usage_limit);
        
        IF FOUND THEN
            IF v_coupon.type = 'percentage' THEN
                v_discount := v_subtotal * (v_coupon.value / 100);
                IF v_coupon.max_discount_amount IS NOT NULL THEN
                    v_discount := LEAST(v_discount, v_coupon.max_discount_amount);
                END IF;
            ELSIF v_coupon.type = 'fixed' THEN
                v_discount := v_coupon.value;
            END IF;
            
            -- Update coupon usage
            UPDATE coupons SET used_count = used_count + 1 WHERE id = v_coupon.id;
        END IF;
    END IF;
    
    -- Calculate total
    p_total := v_subtotal + v_shipping_cost + v_tax - v_discount;
    
    -- Generate order number
    p_order_number := 'ORD-' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDD') || '-' || LPAD(nextval('orders_id_seq')::TEXT, 6, '0');
    
    -- Create order
    INSERT INTO orders (
        order_number, buyer_id, status, subtotal, shipping_cost, tax, discount, total,
        payment_status, payment_method, shipping_address_id, billing_address_id, coupon_id
    ) VALUES (
        p_order_number, p_buyer_id, 'pending', v_subtotal, v_shipping_cost, v_tax, v_discount, p_total,
        'pending', p_payment_method, p_shipping_address_id, p_billing_address_id, v_coupon.id
    ) RETURNING id INTO p_order_id;
    
    -- Move cart items to order items
    FOR v_cart_item IN 
        SELECT c.product_id, c.quantity, p.title, p.price, p.seller_id
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = p_buyer_id
    LOOP
        INSERT INTO order_items (order_id, product_id, seller_id, title, quantity, price, total)
        VALUES (p_order_id, v_cart_item.product_id, v_cart_item.seller_id, v_cart_item.title, 
                v_cart_item.quantity, v_cart_item.price, v_cart_item.price * v_cart_item.quantity);
        
        -- Update inventory
        UPDATE products SET quantity = quantity - v_cart_item.quantity
        WHERE id = v_cart_item.product_id;
    END LOOP;
    
    -- Clear cart
    DELETE FROM cart_items WHERE user_id = p_buyer_id;
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (p_buyer_id, 'order_created', 'Order Created', 
            'Your order ' || p_order_number || ' has been created successfully', 
            '/orders/' || p_order_id);
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
    v_item RECORD;
BEGIN
    -- Get order details
    SELECT * INTO v_order FROM orders WHERE id = p_order_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;
    
    IF v_order.status IN ('cancelled', 'delivered') THEN
        RAISE EXCEPTION 'Cannot cancel order with status: %', v_order.status;
    END IF;
    
    -- Restore inventory
    FOR v_item IN SELECT * FROM order_items WHERE order_id = p_order_id
    LOOP
        UPDATE products SET quantity = quantity + v_item.quantity
        WHERE id = v_item.product_id;
    END LOOP;
    
    -- Update order status
    UPDATE orders SET status = 'cancelled', notes = p_reason WHERE id = p_order_id;
    
    -- Update payment status
    IF v_order.payment_status = 'paid' THEN
        UPDATE orders SET payment_status = 'refunded' WHERE id = p_order_id;
    END IF;
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (v_order.buyer_id, 'order_cancelled', 'Order Cancelled', 
            'Your order ' || v_order.order_number || ' has been cancelled', 
            '/orders/' || p_order_id);
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
DECLARE
    v_order RECORD;
BEGIN
    SELECT * INTO v_order FROM orders WHERE id = p_order_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;
    
    -- Update order
    UPDATE orders 
    SET status = p_new_status,
        tracking_number = COALESCE(p_tracking_number, tracking_number),
        carrier = COALESCE(p_carrier, carrier)
    WHERE id = p_order_id;
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (v_order.buyer_id, 'order_status_update', 'Order Status Updated', 
            'Your order ' || v_order.order_number || ' status: ' || p_new_status, 
            '/orders/' || p_order_id);
END;
$$;

-- ==========================================
-- 2. PRODUCT MANAGEMENT PROCEDURES
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
            rejection_reason = NULL
        WHERE id = p_product_id;
        
        -- Notify seller
        INSERT INTO notifications (user_id, type, title, message, link)
        VALUES (v_product.seller_id, 'product_approved', 'Product Approved', 
                'Your product "' || v_product.title || '" has been approved', 
                '/products/' || p_product_id);
    ELSE
        UPDATE products 
        SET approval_status = 'rejected',
            status = 'rejected',
            rejection_reason = p_reason
        WHERE id = p_product_id;
        
        -- Notify seller
        INSERT INTO notifications (user_id, type, title, message, link)
        VALUES (v_product.seller_id, 'product_rejected', 'Product Rejected', 
                'Your product "' || v_product.title || '" has been rejected. Reason: ' || p_reason, 
                '/products/' || p_product_id);
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

-- ==========================================
-- 3. PAYMENT PROCESSING PROCEDURES
-- ==========================================

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
DECLARE
    v_order RECORD;
BEGIN
    SELECT * INTO v_order FROM orders WHERE id = p_order_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;
    
    -- Create payment record
    INSERT INTO payments (order_id, stripe_payment_id, amount, status, payment_method)
    VALUES (p_order_id, p_stripe_payment_id, p_amount, p_status, p_payment_method);
    
    -- Update order payment status
    IF p_status = 'succeeded' THEN
        UPDATE orders SET payment_status = 'paid', status = 'confirmed' WHERE id = p_order_id;
        
        -- Notify buyer
        INSERT INTO notifications (user_id, type, title, message, link)
        VALUES (v_order.buyer_id, 'payment_success', 'Payment Successful', 
                'Payment for order ' || v_order.order_number || ' was successful', 
                '/orders/' || p_order_id);
    ELSIF p_status = 'failed' THEN
        UPDATE orders SET payment_status = 'failed' WHERE id = p_order_id;
        
        -- Notify buyer
        INSERT INTO notifications (user_id, type, title, message, link)
        VALUES (v_order.buyer_id, 'payment_failed', 'Payment Failed', 
                'Payment for order ' || v_order.order_number || ' failed. Please try again', 
                '/orders/' || p_order_id);
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
    
    -- Update payment status
    UPDATE payments SET status = 'refunded' WHERE order_id = p_order_id;
    UPDATE orders SET payment_status = 'refunded' WHERE id = p_order_id;
    
    -- Notify buyer
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (v_order.buyer_id, 'refund_processed', 'Refund Processed', 
            'Refund of $' || p_refund_amount || ' for order ' || v_order.order_number || ' has been processed', 
            '/orders/' || p_order_id);
END;
$$;

-- Function: Calculate Seller Commission
CREATE OR REPLACE FUNCTION fn_calculate_seller_commission(
    p_order_item_id INT,
    p_commission_rate DECIMAL(5, 2) DEFAULT 10.00
)
RETURNS TABLE(
    seller_id INT,
    item_total DECIMAL(10, 2),
    commission DECIMAL(10, 2),
    seller_amount DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        oi.seller_id,
        oi.total,
        (oi.total * p_commission_rate / 100)::DECIMAL(10, 2),
        (oi.total - (oi.total * p_commission_rate / 100))::DECIMAL(10, 2)
    FROM order_items oi
    WHERE oi.id = p_order_item_id;
END;
$$;

-- ==========================================
-- 4. CART OPERATIONS PROCEDURES
-- ==========================================

-- Procedure: Add to Cart
CREATE OR REPLACE PROCEDURE sp_add_to_cart(
    p_user_id INT,
    p_product_id INT,
    p_quantity INT DEFAULT 1
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_available BOOLEAN;
BEGIN
    -- Check stock availability
    v_available := fn_check_stock_availability(p_product_id, p_quantity);
    
    IF NOT v_available THEN
        RAISE EXCEPTION 'Product not available or insufficient stock';
    END IF;
    
    -- Insert or update cart item
    INSERT INTO cart_items (user_id, product_id, quantity)
    VALUES (p_user_id, p_product_id, p_quantity)
    ON CONFLICT (user_id, product_id) 
    DO UPDATE SET quantity = cart_items.quantity + p_quantity;
END;
$$;

-- Procedure: Update Cart Item
CREATE OR REPLACE PROCEDURE sp_update_cart_item(
    p_user_id INT,
    p_product_id INT,
    p_new_quantity INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_new_quantity <= 0 THEN
        DELETE FROM cart_items WHERE user_id = p_user_id AND product_id = p_product_id;
    ELSE
        -- Check stock
        IF NOT fn_check_stock_availability(p_product_id, p_new_quantity) THEN
            RAISE EXCEPTION 'Insufficient stock';
        END IF;
        
        UPDATE cart_items 
        SET quantity = p_new_quantity
        WHERE user_id = p_user_id AND product_id = p_product_id;
    END IF;
END;
$$;

-- Procedure: Clear Cart
CREATE OR REPLACE PROCEDURE sp_clear_cart(
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM cart_items WHERE user_id = p_user_id;
END;
$$;

-- ==========================================
-- 5. USER OPERATIONS PROCEDURES
-- ==========================================

-- Procedure: Register User
CREATE OR REPLACE PROCEDURE sp_register_user(
    p_email VARCHAR(255),
    p_password_hash VARCHAR(255),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    OUT p_user_id INT,
    p_role VARCHAR(20) DEFAULT 'user'
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO users (email, password_hash, first_name, last_name, role, is_verified, is_active)
    VALUES (p_email, p_password_hash, p_first_name, p_last_name, p_role, FALSE, TRUE)
    RETURNING id INTO p_user_id;
    
    -- Create welcome notification
    INSERT INTO notifications (user_id, type, title, message)
    VALUES (p_user_id, 'welcome', 'Welcome!', 'Welcome to our marketplace!');
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
    
    INSERT INTO notifications (user_id, type, title, message)
    VALUES (p_user_id, 'verified', 'Account Verified', 'Your account has been verified!');
END;
$$;

-- Procedure: Upgrade to Seller
CREATE OR REPLACE PROCEDURE sp_upgrade_to_seller(
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE users SET role = 'seller' WHERE id = p_user_id;
    
    INSERT INTO notifications (user_id, type, title, message)
    VALUES (p_user_id, 'seller_upgrade', 'Seller Account Activated', 
            'You can now start selling on our platform!');
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
    
    IF p_ban THEN
        INSERT INTO notifications (user_id, type, title, message)
        VALUES (p_user_id, 'account_banned', 'Account Suspended', 
                'Your account has been suspended. Reason: ' || COALESCE(p_reason, 'Violation of terms'));
    ELSE
        INSERT INTO notifications (user_id, type, title, message)
        VALUES (p_user_id, 'account_unbanned', 'Account Restored', 
                'Your account has been restored');
    END IF;
END;
$$;

-- ==========================================
-- 6. COUPON SYSTEM PROCEDURES
-- ==========================================

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
    
    IF v_coupon.expires_at IS NOT NULL AND v_coupon.expires_at < CURRENT_TIMESTAMP THEN
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
    IF v_coupon.type = 'percentage' THEN
        v_discount := p_cart_total * (v_coupon.value / 100);
        IF v_coupon.max_discount_amount IS NOT NULL THEN
            v_discount := LEAST(v_discount, v_coupon.max_discount_amount);
        END IF;
    ELSIF v_coupon.type = 'fixed' THEN
        v_discount := v_coupon.value;
    END IF;
    
    RETURN QUERY SELECT TRUE, v_discount, 'Coupon applied successfully';
END;
$$;

-- ==========================================
-- 7. REVIEWS & RATINGS PROCEDURES
-- ==========================================

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
    -- Check if rating is valid
    IF p_rating < 1 OR p_rating > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5';
    END IF;
    
    -- Check if user purchased this product
    SELECT EXISTS(
        SELECT 1 FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.buyer_id = p_user_id 
        AND oi.product_id = p_product_id
        AND o.payment_status = 'paid'
    ) INTO v_verified;
    
    -- Insert review
    INSERT INTO reviews (product_id, user_id, order_id, rating, title, comment, is_verified_purchase)
    VALUES (p_product_id, p_user_id, p_order_id, p_rating, p_title, p_comment, v_verified);
    
    -- Update product average rating
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = p_product_id;
END;
$$;

-- Function: Get Product Average Rating
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
    WHERE product_id = p_product_id;
END;
$$;

-- ==========================================
-- 8. ANALYTICS & REPORTS PROCEDURES
-- ==========================================

-- Function: Get Seller Dashboard Stats
CREATE OR REPLACE FUNCTION fn_get_seller_dashboard(
    p_seller_id INT,
    p_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP - INTERVAL '30 days',
    p_end_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
RETURNS TABLE(
    total_products INT,
    approved_products INT,
    pending_products INT,
    total_sales INT,
    total_revenue DECIMAL(10, 2),
    avg_rating DECIMAL(3, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT p.id)::INT,
        COUNT(DISTINCT CASE WHEN p.approval_status = 'approved' THEN p.id END)::INT,
        COUNT(DISTINCT CASE WHEN p.approval_status = 'pending' THEN p.id END)::INT,
        COUNT(DISTINCT oi.id)::INT,
        COALESCE(SUM(oi.total), 0)::DECIMAL(10, 2),
        COALESCE(AVG(r.rating), 0)::DECIMAL(3, 2)
    FROM products p
    LEFT JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.id AND o.created_at BETWEEN p_start_date AND p_end_date
    LEFT JOIN reviews r ON p.id = r.product_id
    WHERE p.seller_id = p_seller_id;
END;
$$;

-- Function: Get Admin Dashboard Stats
CREATE OR REPLACE FUNCTION fn_get_admin_dashboard(
    p_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP - INTERVAL '30 days',
    p_end_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
RETURNS TABLE(
    total_users INT,
    new_users INT,
    total_sellers INT,
    total_products INT,
    pending_approvals INT,
    total_orders INT,
    completed_orders INT,
    total_revenue DECIMAL(10, 2),
    pending_revenue DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INT FROM users),
        (SELECT COUNT(*)::INT FROM users WHERE created_at BETWEEN p_start_date AND p_end_date),
        (SELECT COUNT(*)::INT FROM users WHERE role = 'seller'),
        (SELECT COUNT(*)::INT FROM products),
        (SELECT COUNT(*)::INT FROM products WHERE approval_status = 'pending'),
        (SELECT COUNT(*)::INT FROM orders WHERE created_at BETWEEN p_start_date AND p_end_date),
        (SELECT COUNT(*)::INT FROM orders WHERE status = 'delivered' AND created_at BETWEEN p_start_date AND p_end_date),
        COALESCE((SELECT SUM(total) FROM orders WHERE payment_status = 'paid' AND created_at BETWEEN p_start_date AND p_end_date), 0)::DECIMAL(10, 2),
        COALESCE((SELECT SUM(total) FROM orders WHERE payment_status = 'pending' AND created_at BETWEEN p_start_date AND p_end_date), 0)::DECIMAL(10, 2);
END;
$$;

-- Function: Get Best Selling Products
CREATE OR REPLACE FUNCTION fn_get_best_selling_products(
    p_limit INT DEFAULT 10,
    p_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP - INTERVAL '30 days',
    p_end_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
RETURNS TABLE(
    product_id INT,
    product_title VARCHAR(255),
    total_sales INT,
    total_revenue DECIMAL(10, 2),
    avg_rating DECIMAL(3, 2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        COUNT(oi.id)::INT,
        SUM(oi.total)::DECIMAL(10, 2),
        COALESCE(AVG(r.rating), 0)::DECIMAL(3, 2)
    FROM products p
    JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    LEFT JOIN reviews r ON p.id = r.product_id
    WHERE o.created_at BETWEEN p_start_date AND p_end_date
    GROUP BY p.id, p.title
    ORDER BY COUNT(oi.id) DESC
    LIMIT p_limit;
END;
$$;

-- Function: Get Revenue Report
CREATE OR REPLACE FUNCTION fn_get_revenue_report(
    p_start_date TIMESTAMP,
    p_end_date TIMESTAMP,
    p_group_by VARCHAR(10) DEFAULT 'day' -- 'day', 'week', 'month'
)
RETURNS TABLE(
    period TEXT,
    total_orders INT,
    total_revenue DECIMAL(10, 2),
    avg_order_value DECIMAL(10, 2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_date_trunc TEXT;
BEGIN
    v_date_trunc := CASE p_group_by
        WHEN 'week' THEN 'week'
        WHEN 'month' THEN 'month'
        ELSE 'day'
    END;
    
    RETURN QUERY EXECUTE format('
        SELECT 
            TO_CHAR(DATE_TRUNC(%L, created_at), ''YYYY-MM-DD''),
            COUNT(*)::INT,
            SUM(total)::DECIMAL(10, 2),
            AVG(total)::DECIMAL(10, 2)
        FROM orders
        WHERE created_at BETWEEN $1 AND $2
        AND payment_status = ''paid''
        GROUP BY DATE_TRUNC(%L, created_at)
        ORDER BY DATE_TRUNC(%L, created_at)
    ', v_date_trunc, v_date_trunc, v_date_trunc)
    USING p_start_date, p_end_date;
END;
$$;

-- ==========================================
-- 9. ADDRESS MANAGEMENT PROCEDURES
-- ==========================================

-- Procedure: Add Address
CREATE OR REPLACE PROCEDURE sp_add_address(
    p_user_id INT,
    p_type VARCHAR(20),
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    p_address_line1 VARCHAR(255),
    p_city VARCHAR(100),
    p_postal_code VARCHAR(20),
    p_country VARCHAR(100),
    p_phone VARCHAR(20),
    OUT p_address_id INT,
    p_is_default BOOLEAN DEFAULT FALSE
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- If this is default, unset other defaults
    IF p_is_default THEN
        UPDATE addresses SET is_default = FALSE 
        WHERE user_id = p_user_id AND type = p_type;
    END IF;
    
    INSERT INTO addresses (
        user_id, type, first_name, last_name, address_line1, 
        city, postal_code, country, phone, is_default
    ) VALUES (
        p_user_id, p_type, p_first_name, p_last_name, p_address_line1,
        p_city, p_postal_code, p_country, p_phone, p_is_default
    ) RETURNING id INTO p_address_id;
END;
$$;

-- Procedure: Set Default Address
CREATE OR REPLACE PROCEDURE sp_set_default_address(
    p_user_id INT,
    p_address_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_type VARCHAR(20);
BEGIN
    -- Get address type
    SELECT type INTO v_type FROM addresses WHERE id = p_address_id AND user_id = p_user_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Address not found';
    END IF;
    
    -- Unset other defaults
    UPDATE addresses SET is_default = FALSE 
    WHERE user_id = p_user_id AND type = v_type;
    
    -- Set new default
    UPDATE addresses SET is_default = TRUE WHERE id = p_address_id;
END;
$$;

-- ==========================================
-- 10. NEW ENHANCED FEATURES PROCEDURES
-- ==========================================

-- Procedure: Soft Delete Product
CREATE OR REPLACE PROCEDURE sp_soft_delete_product(
    p_product_id INT,
    p_admin_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if product exists
    IF NOT EXISTS (SELECT 1 FROM products WHERE id = p_product_id) THEN
        RAISE EXCEPTION 'Product not found';
    END IF;
    
    -- Soft delete the product
    UPDATE products 
    SET deleted_at = CURRENT_TIMESTAMP
    WHERE id = p_product_id AND deleted_at IS NULL;
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, link)
    SELECT 
        seller_id,
        'product_deleted',
        'Product Soft Deleted',
        'Your product "' || title || '" has been archived',
        '/products/' || id
    FROM products
    WHERE id = p_product_id;
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
    -- Restore the product
    UPDATE products 
    SET deleted_at = NULL
    WHERE id = p_product_id AND deleted_at IS NOT NULL;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found or not deleted';
    END IF;
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, link)
    SELECT 
        seller_id,
        'product_restored',
        'Product Restored',
        'Your product "' || title || '" has been restored',
        '/products/' || id
    FROM products
    WHERE id = p_product_id;
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
    -- Check order status
    SELECT status INTO v_order_status FROM orders WHERE id = p_order_id AND buyer_id = p_user_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;
    
    IF v_order_status NOT IN ('delivered', 'completed') THEN
        RAISE EXCEPTION 'Returns can only be requested for delivered orders';
    END IF;
    
    -- Create return request
    INSERT INTO returns (
        order_id, order_item_id, user_id, reason, 
        status, refund_amount
    ) VALUES (
        p_order_id, p_order_item_id, p_user_id, p_reason,
        'requested', p_refund_amount
    ) RETURNING id INTO p_return_id;
    
    -- Create notification for user
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (
        p_user_id,
        'return_requested',
        'Return Request Received',
        'Your return request for order has been submitted',
        '/returns/' || p_return_id
    );
    
    -- Notify admin (get all admins)
    INSERT INTO notifications (user_id, type, title, message, link)
    SELECT 
        id,
        'return_pending',
        'New Return Request',
        'A new return request #' || p_return_id || ' requires review',
        '/admin/returns/' || p_return_id
    FROM users
    WHERE role = 'admin';
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
    v_return RECORD;
    v_new_status VARCHAR(20);
BEGIN
    -- Get return details
    SELECT * INTO v_return FROM returns WHERE id = p_return_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Return not found';
    END IF;
    
    -- Determine new status
    v_new_status := CASE WHEN p_approve THEN 'approved' ELSE 'rejected' END;
    
    -- Update return
    UPDATE returns
    SET 
        status = v_new_status,
        approved_by = p_admin_id,
        approved_at = CURRENT_TIMESTAMP,
        admin_notes = p_admin_notes
    WHERE id = p_return_id;
    
    -- Create notification for user
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (
        v_return.user_id,
        'return_' || v_new_status,
        'Return ' || CASE WHEN p_approve THEN 'Approved' ELSE 'Rejected' END,
        'Your return request #' || p_return_id || ' has been ' || v_new_status,
        '/returns/' || p_return_id
    );
    
    -- If approved, process refund
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
DECLARE
    v_return RECORD;
BEGIN
    -- Get return details
    SELECT * INTO v_return FROM returns WHERE id = p_return_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Return not found';
    END IF;
    
    IF v_return.status != 'processing' THEN
        RAISE EXCEPTION 'Return must be in processing status';
    END IF;
    
    -- Complete return
    UPDATE returns
    SET 
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE id = p_return_id;
    
    -- Create notification
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (
        v_return.user_id,
        'return_completed',
        'Refund Processed',
        'Your refund of $' || v_return.refund_amount || ' has been processed',
        '/returns/' || p_return_id
    );
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
DECLARE
    v_buyer_id INT;
BEGIN
    -- Get buyer ID
    SELECT buyer_id INTO v_buyer_id FROM orders WHERE id = p_order_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order not found';
    END IF;
    
    -- Add shipping event
    INSERT INTO shipping_events (
        order_id, status, location, description, notes,
        carrier, tracking_number, event_time
    ) VALUES (
        p_order_id, p_status, p_location, p_description, p_notes,
        p_carrier, p_tracking_number, p_event_time
    );
    
    -- Update order tracking info if provided
    IF p_tracking_number IS NOT NULL THEN
        UPDATE orders
        SET 
            tracking_number = p_tracking_number,
            carrier = p_carrier
        WHERE id = p_order_id;
    END IF;
    
    -- Create notification for buyer
    INSERT INTO notifications (user_id, type, title, message, link)
    VALUES (
        v_buyer_id,
        'shipping_update',
        'Shipping Update',
        'Your order has been updated: ' || p_status,
        '/orders/' || p_order_id
    );
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
    -- Check if product exists
    IF NOT EXISTS (SELECT 1 FROM products WHERE id = p_product_id) THEN
        RAISE EXCEPTION 'Product not found';
    END IF;
    
    -- Insert variant
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
    
    -- Deactivate if out of stock
    UPDATE product_variants
    SET is_active = FALSE
    WHERE id = p_variant_id AND quantity <= 0;
END;
$$;

-- ==========================================
-- COMMENTS ON PROCEDURES
-- ==========================================

COMMENT ON PROCEDURE sp_create_order IS 'Create order from cart with coupon support';
COMMENT ON PROCEDURE sp_cancel_order IS 'Cancel order and restore inventory';
COMMENT ON PROCEDURE sp_update_order_status IS 'Update order status and send notifications';
COMMENT ON PROCEDURE sp_approve_product IS 'Approve or reject product by admin';
COMMENT ON PROCEDURE sp_update_inventory IS 'Update product inventory';
COMMENT ON PROCEDURE sp_bulk_approve_products IS 'Approve multiple products at once';
COMMENT ON PROCEDURE sp_process_payment IS 'Process payment transaction';
COMMENT ON PROCEDURE sp_process_refund IS 'Process refund for order';
COMMENT ON PROCEDURE sp_add_to_cart IS 'Add product to cart with stock validation';
COMMENT ON PROCEDURE sp_update_cart_item IS 'Update cart item quantity';
COMMENT ON PROCEDURE sp_clear_cart IS 'Clear user cart';
COMMENT ON PROCEDURE sp_register_user IS 'Register new user';
COMMENT ON PROCEDURE sp_verify_user IS 'Verify user email';
COMMENT ON PROCEDURE sp_upgrade_to_seller IS 'Upgrade user to seller role';
COMMENT ON PROCEDURE sp_ban_user IS 'Ban or unban user';
COMMENT ON PROCEDURE sp_add_review IS 'Add product review with purchase verification';
COMMENT ON PROCEDURE sp_add_address IS 'Add user address';
COMMENT ON PROCEDURE sp_set_default_address IS 'Set default shipping/billing address';
COMMENT ON PROCEDURE sp_soft_delete_product IS 'Soft delete product for auditing';
COMMENT ON PROCEDURE sp_restore_product IS 'Restore soft deleted product';
COMMENT ON PROCEDURE sp_request_return IS 'Request product return and refund';
COMMENT ON PROCEDURE sp_process_return IS 'Approve or reject return request';
COMMENT ON PROCEDURE sp_complete_return IS 'Complete return and process refund';
COMMENT ON PROCEDURE sp_add_shipping_event IS 'Add shipping tracking event';
COMMENT ON PROCEDURE sp_add_product_variant IS 'Add product variant (size/color/etc)';
COMMENT ON PROCEDURE sp_update_variant_inventory IS 'Update variant inventory quantity';

-- End of initialization script
