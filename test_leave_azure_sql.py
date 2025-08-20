#!/usr/bin/env python3
"""
Test Azure SQL connection for Leave API and initialize database.
Run this before starting the leave API.
"""
import os
import sys
import pyodbc
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

def test_leave_azure_sql():
    """Test connection to Azure SQL for Leave API and optionally initialize schema."""
    
    # Get connection details (update these with your actual values)
    server = input("Enter your Azure SQL server name (without .database.windows.net): ").strip()
    if not server:
        from os import getenv
        server = f"leave-sql-server-{getenv('SUFFIX', '1234')}"  # default via SUFFIX or 1234
    
    database = input("Enter database name [leave_db]: ").strip()
    if not database:
        database = "leave_db"
    
    username = input("Enter admin username [sqladminuser]: ").strip() 
    if not username:
        username = "sqladminuser"
    
    password = input("Enter admin password: ").strip()
    if not password:
        password = "CHANGE_ME_str0ngP@ss!"  # default from Azure_setup.md
        print(f"Using default password from Azure_setup.md: {password}")
    
    # Build connection string with extended timeout and URL encoding
    encoded_password = quote_plus(password)
    connection_string = (
        f"mssql+pyodbc://{username}:{encoded_password}@{server}.database.windows.net:1433/{database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30&ConnectTimeout=30"
    )
    
    print(f"\nTesting connection to: {server}.database.windows.net/{database}")
    print(f"Connection string: {connection_string.replace(encoded_password, '***')}")
    
    try:
        # Test with SQLAlchemy (same as the app uses)
        engine = create_engine(
            connection_string, 
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT @@VERSION"))
            version_row = result.fetchone()
            if version_row:
                version = version_row[0]
                print(f"✅ Connected successfully!")
                print(f"SQL Server version: {version}")
            else:
                print(f"✅ Connected successfully!")
                print("SQL Server version: Unable to retrieve")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dbo' 
                AND TABLE_NAME IN ('employees', 'leave_requests', 'leave_balances')
            """))
            count_row = result.fetchone()
            table_count = count_row[0] if count_row else 0
            print(f"Found {table_count}/3 leave tables")
            
            if table_count == 0:
                print("\n🔧 No leave tables found. Would you like to initialize them?")
                init = input("Initialize schema? (y/N): ").strip().lower()
                if init in ['y', 'yes']:
                    initialize_leave_schema(conn)
            
            # Set environment variable for the app
            os.environ['LEAVE_DATABASE_URL'] = connection_string
            print(f"\n✅ Set LEAVE_DATABASE_URL environment variable")
            print("You can now run: uvicorn leave_app.api.main:app --host 0.0.0.0 --port 8001")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your server name, username, and password")
        print("2. Ensure your IP (110.226.180.28) is allowed in Azure SQL firewall")
        print("   Run: az sql server firewall-rule create --resource-group <rg> --server <server> --name AllowMyIP --start-ip-address 110.226.180.28 --end-ip-address 110.226.180.28")
        print("3. Verify the database exists")
        print("4. Check if ODBC Driver 18 is installed: python -c \"import pyodbc; print(pyodbc.drivers())\"")
        print("5. Try connecting with a simpler connection string or different driver")
        print("6. Check Azure SQL server logs in Azure Portal")
        return False
    
    return True

def initialize_leave_schema(conn):
    """Initialize the leave database schema."""
    try:
        # Read and execute schema.sql
        with open('leave_app/sql/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute each statement separately (split by GO or semicolon)
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                print(f"Executing: {statement[:50]}...")
                conn.execute(text(statement))
        
        # Read and execute seed.sql
        with open('leave_app/sql/seed.sql', 'r') as f:
            seed_sql = f.read()
        
        statements = [s.strip() for s in seed_sql.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                print(f"Executing: {statement[:50]}...")
                conn.execute(text(statement))
        
        conn.commit()
        print("✅ Schema and seed data initialized successfully!")
        
    except Exception as e:
        print(f"❌ Schema initialization failed: {e}")
        conn.rollback()

if __name__ == "__main__":
    test_leave_azure_sql()
