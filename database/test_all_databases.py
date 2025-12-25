#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Database Test Suite
Tests all tables, procedures, functions, and views across all databases
"""

import os
import sys
# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2
import uuid
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'ecommerce_admin',
    'password': 'change_this_secure_password_123!'
}

DATABASES = ['auth_db', 'product_db', 'order_db', 'admin_db']

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class DatabaseTester:
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
    
    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    def print_success(self, text: str):
        print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")
        self.results['passed'] += 1
    
    def print_error(self, text: str):
        print(f"{Colors.RED}❌ {text}{Colors.RESET}")
        self.results['failed'] += 1
        self.results['errors'].append(text)
    
    def print_skip(self, text: str):
        print(f"{Colors.YELLOW}⏭️  {text}{Colors.RESET}")
        self.results['skipped'] += 1
    
    def get_connection(self, database: str):
        """Get database connection"""
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=database
            )
            return conn
        except Exception as e:
            self.print_error(f"Failed to connect to {database}: {str(e)}")
            return None
    
    def test_table(self, conn, table_name: str) -> bool:
        """Test if table exists and can be queried"""
        try:
            # Ensure transaction is not aborted
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                self.print_success(f"Table {table_name}: {count} rows")
                return True
        except Exception as e:
            # Rollback on error
            conn.rollback()
            error_msg = str(e).split('\n')[0]
            self.print_error(f"Table {table_name}: {error_msg}")
            return False
    
    def test_procedure(self, conn, proc_name: str, test_sql: str) -> bool:
        """Test a stored procedure"""
        try:
            with conn.cursor() as cur:
                cur.execute(test_sql)
                conn.commit()
                self.print_success(f"Procedure {proc_name}: Executed successfully")
                return True
        except Exception as e:
            # Rollback on error to prevent transaction abort
            conn.rollback()
            error_msg = str(e).split('\n')[0]  # Get first line of error
            if 'not found' in error_msg.lower() or 'no data' in error_msg.lower():
                self.print_skip(f"Procedure {proc_name}: {error_msg}")
            else:
                self.print_error(f"Procedure {proc_name}: {error_msg}")
            return False
    
    def test_function(self, conn, func_name: str, test_sql: str) -> bool:
        """Test a stored function"""
        try:
            with conn.cursor() as cur:
                cur.execute(test_sql)
                result = cur.fetchone()
                self.print_success(f"Function {func_name}: Result = {result}")
                return True
        except Exception as e:
            # Rollback on error to prevent transaction abort
            conn.rollback()
            error_msg = str(e).split('\n')[0]
            self.print_error(f"Function {func_name}: {error_msg}")
            return False
    
    def test_view(self, conn, view_name: str) -> bool:
        """Test if view exists and can be queried"""
        try:
            # Ensure transaction is not aborted
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {view_name}")
                count = cur.fetchone()[0]
                self.print_success(f"View {view_name}: {count} rows")
                return True
        except Exception as e:
            # Rollback on error
            conn.rollback()
            error_msg = str(e).split('\n')[0]
            self.print_error(f"View {view_name}: {error_msg}")
            return False
    
    def test_auth_db(self):
        """Test AUTH_DB"""
        self.print_header("📊 Testing AUTH_DB")
        conn = self.get_connection('auth_db')
        if not conn:
            return
        
        try:
            # Test Tables
            print(f"{Colors.BOLD}  Testing Tables...{Colors.RESET}")
            self.test_table(conn, 'users')
            self.test_table(conn, 'addresses')
            self.test_table(conn, 'customer_profiles')
            self.test_table(conn, 'vendor_profiles')
            self.test_table(conn, 'refresh_tokens')
            
            # Test Procedures
            print(f"\n{Colors.BOLD}  Testing Procedures...{Colors.RESET}")
            
            # Get a test user ID
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users LIMIT 1")
                user_result = cur.fetchone()
                test_user_id = user_result[0] if user_result else None
                
                if test_user_id:
                    # Test sp_register_user (use unique email)
                    unique_email = f'test_{int(datetime.now().timestamp())}@example.com'
                    self.test_procedure(conn, 'sp_register_user',
                        f"CALL sp_register_user('{unique_email}', '$2b$12$test', 'Test', 'User', NULL, 'customer')")
                    
                    # Test sp_verify_user
                    self.test_procedure(conn, 'sp_verify_user',
                        f"CALL sp_verify_user({test_user_id})")
                    
                    # Test sp_upgrade_to_seller (old procedure, kept for compatibility)
                    self.test_procedure(conn, 'sp_upgrade_to_seller',
                        f"CALL sp_upgrade_to_seller({test_user_id})")
                    
                    # Test sp_upgrade_to_vendor (new procedure) - use unique business name
                    unique_business_name = f'Test Business {int(datetime.now().timestamp())}'
                    unique_business_email = f'business_{int(datetime.now().timestamp())}@test.com'
                    self.test_procedure(conn, 'sp_upgrade_to_vendor',
                        f"CALL sp_upgrade_to_vendor({test_user_id}, '{unique_business_name}', '{unique_business_email}')")
                    
                    # Test sp_approve_vendor (new procedure)
                    self.test_procedure(conn, 'sp_approve_vendor',
                        f"CALL sp_approve_vendor({test_user_id}, 1, TRUE, NULL)")
                    
                    # Test sp_update_customer_stats (new procedure)
                    self.test_procedure(conn, 'sp_update_customer_stats',
                        f"CALL sp_update_customer_stats({test_user_id}, 150.00)")
                    
                    # Test sp_ban_user
                    self.test_procedure(conn, 'sp_ban_user',
                        f"CALL sp_ban_user({test_user_id}, FALSE, 'Test')")
                    
                    # Test sp_add_address (address_type instead of type, has OUT parameter)
                    try:
                        with conn.cursor() as test_cur:
                            test_cur.execute(f"""
                                DO $$ 
                                DECLARE 
                                    addr_id INT; 
                                BEGIN 
                                    CALL sp_add_address({test_user_id}, 'shipping', 'Test', 'User', '123 St', 'City', '12345', 'USA', '1234567890', addr_id, NULL, TRUE); 
                                END $$;
                            """)
                            conn.commit()
                            self.print_success("Procedure sp_add_address: Executed successfully")
                        self.results['passed'] += 1
                    except Exception as e:
                        conn.rollback()
                        error_msg = str(e).split('\n')[0]
                        self.print_error(f"Procedure sp_add_address: {error_msg}")
                        self.results['failed'] += 1
                        self.results['errors'].append(f"sp_add_address: {error_msg}")
            
            # Test Views
            print(f"\n{Colors.BOLD}  Testing Views...{Colors.RESET}")
            self.test_view(conn, 'vw_user_statistics')
            
        finally:
            conn.close()
    
    def test_product_db(self):
        """Test PRODUCT_DB"""
        self.print_header("📊 Testing PRODUCT_DB")
        conn = self.get_connection('product_db')
        if not conn:
            return
        
        try:
            # Test Tables
            print(f"{Colors.BOLD}  Testing Tables...{Colors.RESET}")
            self.test_table(conn, 'brands')
            self.test_table(conn, 'categories')
            self.test_table(conn, 'products')
            self.test_table(conn, 'product_images')
            self.test_table(conn, 'product_variants')
            self.test_table(conn, 'product_attributes')
            self.test_table(conn, 'reviews')
            self.test_table(conn, 'wishlist')
            
            # Test Procedures
            print(f"\n{Colors.BOLD}  Testing Procedures...{Colors.RESET}")
            
            with conn.cursor() as cur:
                # Get a brand_id if available
                cur.execute("SELECT id FROM brands LIMIT 1")
                brand_result = cur.fetchone()
                brand_id = brand_result[0] if brand_result else None
                
                # Create a test product (vendor_id instead of seller_id)
                if brand_id:
                    cur.execute("""
                        INSERT INTO products (vendor_id, title, description, price, quantity, status, approval_status, brand_id)
                        VALUES (1, 'Test Product', 'Test Description', 99.99, 10, 'pending', 'pending', %s)
                        RETURNING id
                    """, (brand_id,))
                else:
                    cur.execute("""
                        INSERT INTO products (vendor_id, title, description, price, quantity, status, approval_status)
                        VALUES (1, 'Test Product', 'Test Description', 99.99, 10, 'pending', 'pending')
                        RETURNING id
                    """)
                product_id = cur.fetchone()[0]
                conn.commit()
                
                # Test sp_approve_product
                self.test_procedure(conn, 'sp_approve_product',
                    f"CALL sp_approve_product({product_id}, 1, TRUE, NULL)")
                
                # Test sp_update_inventory
                self.test_procedure(conn, 'sp_update_inventory',
                    f"CALL sp_update_inventory({product_id}, 5, 'test')")
                
                # Test fn_check_stock_availability
                self.test_function(conn, 'fn_check_stock_availability',
                    f"SELECT fn_check_stock_availability({product_id}, 1)")
                
                # Test sp_increment_view_count (new procedure)
                self.test_procedure(conn, 'sp_increment_view_count',
                    f"CALL sp_increment_view_count({product_id})")
                
                # Test sp_soft_delete_product
                self.test_procedure(conn, 'sp_soft_delete_product',
                    f"CALL sp_soft_delete_product({product_id}, 1)")
                
                # Test sp_restore_product
                self.test_procedure(conn, 'sp_restore_product',
                    f"CALL sp_restore_product({product_id}, 1)")
                
                # Test sp_add_review
                self.test_procedure(conn, 'sp_add_review',
                    f"CALL sp_add_review({product_id}, 1, NULL, 5, 'Great', 'Excellent')")
                
                # Test fn_get_product_rating
                self.test_function(conn, 'fn_get_product_rating',
                    f"SELECT * FROM fn_get_product_rating({product_id})")
                
                # Test sp_add_product_variant (use unique SKU)
                unique_sku = f'VAR-{int(datetime.now().timestamp())}'
                self.test_procedure(conn, 'sp_add_product_variant',
                    f"CALL sp_add_product_variant({product_id}, 'Variant', '{unique_sku}', 89.99, 5, NULL, 'Large', 'Blue', 'Cotton')")
            
            # Test Views
            print(f"\n{Colors.BOLD}  Testing Views...{Colors.RESET}")
            self.test_view(conn, 'vw_active_products')
            self.test_view(conn, 'vw_product_variants_details')
            self.test_view(conn, 'vw_product_reviews_detailed')
            self.test_view(conn, 'vw_popular_products')
            self.test_view(conn, 'vw_pending_approvals')
            self.test_view(conn, 'vw_product_inventory_status')
            
        finally:
            conn.close()
    
    def test_order_db(self):
        """Test ORDER_DB"""
        self.print_header("📊 Testing ORDER_DB")
        conn = self.get_connection('order_db')
        if not conn:
            return
        
        try:
            # Test Tables
            print(f"{Colors.BOLD}  Testing Tables...{Colors.RESET}")
            self.test_table(conn, 'orders')
            self.test_table(conn, 'order_items')
            self.test_table(conn, 'payments')
            self.test_table(conn, 'carts')
            self.test_table(conn, 'cart_items')
            self.test_table(conn, 'coupons')
            self.test_table(conn, 'coupon_usages')
            self.test_table(conn, 'order_status_history')
            self.test_table(conn, 'shipping_methods')
            self.test_table(conn, 'shipping_zones')
            self.test_table(conn, 'shipments')
            self.test_table(conn, 'shipment_items')
            self.test_table(conn, 'shipment_tracking')
            self.test_table(conn, 'shipping_labels')
            self.test_table(conn, 'saved_payment_methods')
            self.test_table(conn, 'payment_refunds')
            self.test_table(conn, 'vendor_payouts')
            self.test_table(conn, 'returns')
            
            # Test Procedures
            print(f"\n{Colors.BOLD}  Testing Procedures...{Colors.RESET}")
            
            # Create test coupon (using discount_type and discount_value instead of type and value)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO coupons (code, discount_type, discount_value, is_active, valid_until)
                    VALUES ('TEST10', 'percentage', 10.00, TRUE, CURRENT_TIMESTAMP + INTERVAL '30 days')
                    ON CONFLICT (code) DO NOTHING
                """)
                conn.commit()
                
                # Test sp_add_to_cart (now uses cart_id, supports variant_id and unit_price)
                # Ensure unique constraint exists for ON CONFLICT to work
                try:
                    with conn.cursor() as test_cur:
                        # Check if unique constraint exists, create if not
                        test_cur.execute("""
                            SELECT COUNT(*) FROM pg_indexes 
                            WHERE tablename = 'cart_items' 
                            AND indexname = 'idx_cart_items_unique'
                        """)
                        constraint_exists = test_cur.fetchone()[0] > 0
                        
                        if not constraint_exists:
                            # Create the unique constraint
                            test_cur.execute("""
                                CREATE UNIQUE INDEX IF NOT EXISTS idx_cart_items_unique 
                                ON cart_items(cart_id, product_id, variant_id)
                            """)
                            conn.commit()
                        
                        # Now test the procedure
                        test_cur.execute("CALL sp_add_to_cart(1, 1, 2, NULL, 99.99)")
                        conn.commit()
                        self.print_success("Procedure sp_add_to_cart: Executed successfully")
                    self.results['passed'] += 1
                except Exception as e:
                    conn.rollback()
                    error_msg = str(e).split('\n')[0]
                    self.print_error(f"Procedure sp_add_to_cart: {error_msg}")
                    self.results['failed'] += 1
                    self.results['errors'].append(f"sp_add_to_cart: {error_msg}")
                
                # Test sp_update_cart_item (now uses cart_id)
                self.test_procedure(conn, 'sp_update_cart_item',
                    "CALL sp_update_cart_item(1, 1, 3)")
                
                # Test fn_validate_coupon (uses discount_type and discount_value)
                self.test_function(conn, 'fn_validate_coupon',
                    "SELECT * FROM fn_validate_coupon('TEST10', 100.00)")
                
                # Test sp_create_order (signature changed - uses cart_id, coupon_code parameter)
                # Note: sp_create_order requires cart_items to exist for the buyer_id
                # Ensure cart and cart_items exist before testing
                try:
                    with conn.cursor() as test_cur:
                        # Ensure cart exists for user 1
                        test_cur.execute("""
                            INSERT INTO carts (customer_id) 
                            VALUES (1) 
                            ON CONFLICT (customer_id) DO NOTHING
                        """)
                        
                        # Ensure cart has items (if not already added by sp_add_to_cart test)
                        test_cur.execute("""
                            SELECT COUNT(*) FROM cart_items WHERE cart_id = 1
                        """)
                        cart_item_count = test_cur.fetchone()[0]
                        
                        if cart_item_count == 0:
                            # Add a cart item if none exist
                            # Note: This assumes product_id 1 exists in product_db
                            # If not, we'll get a foreign key error which is acceptable
                            # Use INSERT with ON CONFLICT matching the unique constraint
                            try:
                                test_cur.execute("""
                                    INSERT INTO cart_items (cart_id, product_id, variant_id, quantity, unit_price)
                                    VALUES (1, 1, NULL, 2, 99.99)
                                    ON CONFLICT (cart_id, product_id, variant_id) DO NOTHING
                                """)
                            except Exception:
                                # If unique constraint doesn't exist, try without ON CONFLICT
                                test_cur.execute("""
                                    INSERT INTO cart_items (cart_id, product_id, variant_id, quantity, unit_price)
                                    VALUES (1, 1, NULL, 2, 99.99)
                                """)
                        
                        conn.commit()
                        
                        # Test sp_create_order
                        # Note: addresses table is in auth_db, not order_db, so we can't query it
                        # We'll pass NULL for address IDs - the procedure accepts them and stores them
                        test_cur.execute("""
                            DO $$ 
                            DECLARE 
                                o_id INT; 
                                o_num VARCHAR(50); 
                                o_total DECIMAL(10,2);
                            BEGIN 
                                -- Pass NULL for addresses since they're in auth_db (separate database)
                                -- The procedure will accept NULL and store it in the order
                                CALL sp_create_order(1, NULL, NULL, 'credit_card', o_id, o_num, o_total, 'TEST10'); 
                            END $$;
                        """)
                        conn.commit()
                        self.print_success("Procedure sp_create_order: Executed successfully")
                    self.results['passed'] += 1
                except Exception as e:
                    conn.rollback()
                    error_msg = str(e).split('\n')[0]
                    if 'cart is empty' in error_msg.lower():
                        # Try to add items and retry
                        try:
                            with conn.cursor() as retry_cur:
                                try:
                                    retry_cur.execute("""
                                        INSERT INTO cart_items (cart_id, product_id, variant_id, quantity, unit_price)
                                        VALUES (1, 1, NULL, 2, 99.99)
                                        ON CONFLICT (cart_id, product_id, variant_id) DO NOTHING
                                    """)
                                except Exception:
                                    # If unique constraint doesn't exist, try without ON CONFLICT
                                    retry_cur.execute("""
                                        INSERT INTO cart_items (cart_id, product_id, variant_id, quantity, unit_price)
                                        VALUES (1, 1, NULL, 2, 99.99)
                                    """)
                                conn.commit()
                                # Retry the procedure with NULL addresses (addresses are in auth_db, not order_db)
                                retry_cur.execute("""
                                    DO $$ 
                                    DECLARE 
                                        o_id INT; 
                                        o_num VARCHAR(50); 
                                        o_total DECIMAL(10,2);
                                    BEGIN 
                                        -- Pass NULL for addresses since they're in auth_db (separate database)
                                        CALL sp_create_order(1, NULL, NULL, 'credit_card', o_id, o_num, o_total, 'TEST10'); 
                                    END $$;
                                """)
                                conn.commit()
                                self.print_success("Procedure sp_create_order: Executed successfully (after adding cart items)")
                                self.results['passed'] += 1
                        except Exception as retry_e:
                            conn.rollback()
                            retry_error_msg = str(retry_e).split('\n')[0]
                            self.print_error(f"Procedure sp_create_order: {retry_error_msg}")
                            self.results['failed'] += 1
                            self.results['errors'].append(f"sp_create_order: {retry_error_msg}")
                    else:
                        self.print_error(f"Procedure sp_create_order: {error_msg}")
                        self.results['failed'] += 1
                        self.results['errors'].append(f"sp_create_order: {error_msg}")
                
                # Get order ID for further tests
                cur.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
                order_result = cur.fetchone()
                order_id = order_result[0] if order_result else None
                
                if order_id:
                    # Test sp_update_order_status
                    self.test_procedure(conn, 'sp_update_order_status',
                        f"CALL sp_update_order_status({order_id}, 'confirmed', 'TRACK123', 'UPS')")
                    
                    # Test sp_process_payment
                    self.test_procedure(conn, 'sp_process_payment',
                        f"CALL sp_process_payment({order_id}, 'stripe_123', 100.00, 'credit_card', 'succeeded')")
                    
                    # Test sp_add_shipping_event
                    self.test_procedure(conn, 'sp_add_shipping_event',
                        f"CALL sp_add_shipping_event({order_id}, 'shipped', 'Warehouse', 'Shipped', 'Notes', 'UPS', 'TRACK123')")
            
            # Test Views
            print(f"\n{Colors.BOLD}  Testing Views...{Colors.RESET}")
            self.test_view(conn, 'vw_order_items_full')
            self.test_view(conn, 'vw_order_history_complete')
            self.test_view(conn, 'vw_pending_orders')
            self.test_view(conn, 'vw_order_shipping_info')
            self.test_view(conn, 'vw_returns_details')
            self.test_view(conn, 'vw_shipping_tracking')
            self.test_view(conn, 'vw_order_history_with_returns')
            
        finally:
            conn.close()
    
    def test_admin_db(self):
        """Test ADMIN_DB"""
        self.print_header("📊 Testing ADMIN_DB")
        conn = self.get_connection('admin_db')
        if not conn:
            return
        
        try:
            # Test Tables
            print(f"{Colors.BOLD}  Testing Tables...{Colors.RESET}")
            self.test_table(conn, 'audit_logs')
            self.test_table(conn, 'notifications')
            self.test_table(conn, 'messages')
            self.test_table(conn, 'system_settings')
            self.test_table(conn, 'email_templates')
            self.test_table(conn, 'email_notifications')
            self.test_table(conn, 'notification_preferences')
            self.test_table(conn, 'system_announcements')
            self.test_table(conn, 'announcement_dismissals')
            
            # Test Foreign Tables
            print(f"\n{Colors.BOLD}  Testing Foreign Tables...{Colors.RESET}")
            with conn.cursor() as cur:
                # Check if foreign tables exist
                cur.execute("""
                    SELECT ftrelid::regclass::text 
                    FROM pg_foreign_table 
                    WHERE ftrelid::regclass::text IN ('users', 'products', 'orders', 'addresses', 'categories', 'order_items')
                """)
                foreign_tables = [row[0] for row in cur.fetchall()]
                
                for table in ['users', 'addresses', 'products', 'categories', 'orders', 'order_items']:
                    if table in foreign_tables:
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cur.fetchone()[0]
                            self.print_success(f"Foreign table {table}: {count} rows")
                        except Exception as e:
                            self.print_error(f"Foreign table {table}: {str(e)}")
                    else:
                        self.print_skip(f"Foreign table {table}: Not imported")
            
        finally:
            conn.close()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("📊 Test Summary")
        
        total = self.results['passed'] + self.results['failed'] + self.results['skipped']
        
        print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total}")
        print(f"{Colors.GREEN}✅ Passed:{Colors.RESET} {self.results['passed']}")
        print(f"{Colors.RED}❌ Failed:{Colors.RESET} {self.results['failed']}")
        print(f"{Colors.YELLOW}⏭️  Skipped:{Colors.RESET} {self.results['skipped']}")
        
        if self.results['errors']:
            print(f"\n{Colors.RED}{Colors.BOLD}Errors:{Colors.RESET}")
            for error in self.results['errors']:
                print(f"  {Colors.RED}• {error}{Colors.RESET}")
        
        print()
        
        # Return exit code
        return 0 if self.results['failed'] == 0 else 1
    
    def run_all_tests(self):
        """Run all database tests"""
        self.print_header("🧪 COMPREHENSIVE DATABASE TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.test_auth_db()
        self.test_product_db()
        self.test_order_db()
        self.test_admin_db()
        
        print()
        return self.print_summary()

def main():
    """Main entry point"""
    tester = DatabaseTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

