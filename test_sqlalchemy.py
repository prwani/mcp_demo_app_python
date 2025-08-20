#!/usr/bin/env python3
"""
Simple SQLAlchemy Azure SQL test
"""
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

def test_sqlalchemy_connection():
    # Connection details
    import os
    suffix = os.getenv("SUFFIX", "1234")
    server = f"timesheet-sql-server-{suffix}"
    database = "timesheet_db"
    username = "sqladminuser"
    password = "CHANGE_ME_str0ngP@ss!"
    
    # URL encode the password
    encoded_password = quote_plus(password)
    
    # Try different SQLAlchemy connection formats
    connection_strings = [
        # Format 1: With timeout parameters in URL
        f"mssql+pyodbc://{username}:{encoded_password}@{server}.database.windows.net:1433/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30&ConnectTimeout=30",
        
        # Format 2: With timeout in connect_args
        f"mssql+pyodbc://{username}:{encoded_password}@{server}.database.windows.net:1433/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no",
        
        # Format 3: Using ODBC Driver 17
        f"mssql+pyodbc://{username}:{encoded_password}@{server}.database.windows.net:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        print(f"\nTrying SQLAlchemy format {i}...")
        print(f"Connection string: {conn_str.replace(encoded_password, '***')}")
        
        try:
            if i == 2:
                # For format 2, use connect_args for timeout
                engine = create_engine(
                    conn_str,
                    connect_args={
                        "timeout": 30,
                        "autocommit": True
                    },
                    pool_pre_ping=True
                )
            else:
                engine = create_engine(
                    conn_str,
                    pool_pre_ping=True
                )
            
            print("Engine created, testing connection...")
            with engine.connect() as conn:
                result = conn.execute(text("SELECT @@VERSION"))
                version_row = result.fetchone()
                if version_row:
                    version = version_row[0]
                    print(f"✅ SUCCESS with SQLAlchemy format {i}!")
                    print(f"SQL Server version: {version[:100]}...")
                    return conn_str
                else:
                    print(f"✅ Connected but no version info")
                    return conn_str
                    
        except Exception as e:
            print(f"❌ Failed with format {i}: {e}")
    
    return None

if __name__ == "__main__":
    working_conn = test_sqlalchemy_connection()
    if working_conn:
        print(f"\n✅ Found working SQLAlchemy connection string!")
    else:
        print(f"\n❌ No working SQLAlchemy connection found")
