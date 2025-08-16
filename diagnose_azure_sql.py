#!/usr/bin/env python3
"""
Azure SQL Connection Diagnostic Tool
This script tests various connection parameters to help diagnose connection issues.
"""
import pyodbc
import socket
import sys
from urllib.parse import quote_plus

def test_basic_connectivity():
    """Test basic network connectivity to Azure SQL."""
    print("🔍 Testing basic connectivity...")
    
    # Get server name from user
    server = input("Enter your Azure SQL server name (without .database.windows.net): ").strip()
    if not server:
        server = "timesheet-sql-server-7859"  # default
    
    full_server = f"{server}.database.windows.net"
    port = 1433
    
    try:
        print(f"Testing connection to {full_server}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((full_server, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Network connection to {full_server}:{port} is working")
            return True
        else:
            print(f"❌ Cannot reach {full_server}:{port}")
            print("This usually means firewall rules are blocking the connection")
            return False
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def test_odbc_drivers():
    """Test available ODBC drivers."""
    print("\n🔍 Testing ODBC drivers...")
    try:
        drivers = pyodbc.drivers()
        print("Available ODBC drivers:")
        for driver in drivers:
            print(f"  - {driver}")
        
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
        if sql_server_drivers:
            print(f"✅ Found {len(sql_server_drivers)} SQL Server driver(s)")
            return sql_server_drivers
        else:
            print("❌ No SQL Server drivers found")
            return []
    except Exception as e:
        print(f"❌ Error checking ODBC drivers: {e}")
        return []

def test_connection_strings(server, database, username, password):
    """Test various connection string formats."""
    print("\n🔍 Testing different connection string formats...")
    
    # URL encode the password to handle special characters
    encoded_password = quote_plus(password)
    
    # Different connection string formats to try
    connection_formats = [
        # Format 1: ODBC Driver 18 with encryption
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server}.database.windows.net;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
        
        # Format 2: ODBC Driver 17 with encryption
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server}.database.windows.net;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
        
        # Format 3: ODBC Driver 18 without strict encryption
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server}.database.windows.net;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;",
        
        # Format 4: Using port explicitly
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server}.database.windows.net,1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
    ]
    
    for i, conn_str in enumerate(connection_formats, 1):
        print(f"\nTrying format {i}...")
        # Hide password in output
        safe_conn_str = conn_str.replace(password, "***")
        print(f"Connection string: {safe_conn_str}")
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version_row = cursor.fetchone()
            if version_row:
                version = version_row[0]
                print(f"✅ SUCCESS! Connected with format {i}")
                print(f"SQL Server version: {version[:100]}...")
            else:
                print(f"✅ SUCCESS! Connected with format {i}")
                print("SQL Server version: Unable to retrieve")
            cursor.close()
            conn.close()
            return conn_str
        except Exception as e:
            print(f"❌ Failed with format {i}: {e}")
    
    return None

def main():
    """Main diagnostic function."""
    print("Azure SQL Connection Diagnostic Tool")
    print("=" * 40)
    
    # Test 1: Basic connectivity
    if not test_basic_connectivity():
        print("\n💡 Next steps:")
        print("1. Check your Azure SQL firewall rules")
        print("2. Ensure your current IP (110.226.180.28) is whitelisted")
        print("3. Use Azure CLI: az sql server firewall-rule create --resource-group <rg> --server <server> --name AllowMyIP --start-ip-address 110.226.180.28 --end-ip-address 110.226.180.28")
        return
    
    # Test 2: ODBC drivers
    drivers = test_odbc_drivers()
    if not drivers:
        print("\n💡 Next steps:")
        print("1. Install ODBC Driver for SQL Server")
        print("2. On Ubuntu/Debian: sudo apt-get install msodbcsql18")
        return
    
    # Test 3: Choose which database to test
    print("\n🔍 Which database would you like to test?")
    print("1. Timesheet database (timesheet-sql-server-7859, timesheet_db)")
    print("2. Leave database (leave-sql-server-7859, leave_db)")
    print("3. Custom database")
    
    choice = input("Enter your choice (1/2/3) [1]: ").strip()
    if not choice:
        choice = "1"
    
    if choice == "1":
        server = "timesheet-sql-server-7859"
        database = "timesheet_db"
    elif choice == "2":
        server = "leave-sql-server-7859" 
        database = "leave_db"
    else:
        server = input("Enter your Azure SQL server name (without .database.windows.net): ").strip()
        if not server:
            server = "timesheet-sql-server-7859"
        database = input("Enter database name: ").strip()
        if not database:
            database = "timesheet_db"
    
    username = input("Enter admin username [sqladminuser]: ").strip()
    if not username:
        username = "sqladminuser"
    
    password = input("Enter admin password: ").strip()
    if not password:
        password = "CHANGE_ME_str0ngP@ss!"
        print(f"Using default password from Azure_setup.md")
    
    # Test 4: Connection strings
    working_conn_str = test_connection_strings(server, database, username, password)
    
    if working_conn_str:
        print(f"\n✅ Found working connection!")
        print("You can use this connection string format for your application.")
        
        # Convert to SQLAlchemy format
        encoded_password = quote_plus(password)
        sqlalchemy_url = f"mssql+pyodbc://{username}:{encoded_password}@{server}.database.windows.net:1433/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"
        print(f"\nSQLAlchemy URL format:")
        print(sqlalchemy_url.replace(encoded_password, "***"))
        
        # Set appropriate environment variable
        if "leave" in database.lower():
            print(f"\nTo use with Leave API, set:")
            print(f"export LEAVE_DATABASE_URL=\"{sqlalchemy_url.replace(encoded_password, password)}\"")
        elif "timesheet" in database.lower():
            print(f"\nTo use with Timesheet API, set:")
            print(f"export TIMESHEET_DATABASE_URL=\"{sqlalchemy_url.replace(encoded_password, password)}\"")
        else:
            print(f"\nTo use this connection string, set the appropriate environment variable")
    else:
        print(f"\n❌ No working connection string found")
        print("\n💡 Next steps:")
        print("1. Double-check your server name, database name, username, and password")
        print("2. Verify the database exists in Azure Portal")
        print("3. Check Azure SQL server firewall rules")
        print("4. Try connecting with Azure Data Studio or SQL Server Management Studio")

if __name__ == "__main__":
    main()
