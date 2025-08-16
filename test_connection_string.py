#!/usr/bin/env python3
"""
Test the managed identity connection string format locally
"""

import os
from urllib.parse import urlparse, parse_qs

# Test the connection string format we're using
connection_string = "mssql+pyodbc://leave-sql-server-7859.database.windows.net:1433/leave_db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Authentication=ActiveDirectoryMsi"

print("🔍 Analyzing connection string:")
print(f"Connection string: {connection_string}")
print()

# Parse the URL
parsed = urlparse(connection_string)
print(f"Scheme: {parsed.scheme}")
print(f"Username: {parsed.username}")
print(f"Password: {parsed.password}")
print(f"Hostname: {parsed.hostname}")
print(f"Port: {parsed.port}")
print(f"Database: {parsed.path.lstrip('/')}")
print()

# Parse query parameters
params = parse_qs(parsed.query)
print("Query parameters:")
for key, values in params.items():
    print(f"  {key}: {values[0] if values else 'None'}")

print()

# Check for conflicts
has_auth = any('authentication' in key.lower() for key in params.keys())
has_integrated = any('integrated' in key.lower() for key in params.keys())
has_trusted = any('trusted' in key.lower() for key in params.keys())
has_username = parsed.username is not None

print("🔍 Conflict Analysis:")
print(f"  Has Authentication param: {has_auth}")
print(f"  Has Integrated Security: {has_integrated}")
print(f"  Has Trusted Connection: {has_trusted}")
print(f"  Has Username: {has_username}")

if has_auth and (has_integrated or has_trusted):
    print("  ❌ CONFLICT: Authentication param conflicts with Integrated/Trusted")
elif has_auth and has_username:
    print("  ❌ CONFLICT: Authentication=ActiveDirectory* conflicts with username")
else:
    print("  ✅ No obvious conflicts detected")

print()
print("💡 For managed identity:")
print("  - No username/password should be provided")
print("  - Use Authentication=ActiveDirectoryMsi")
print("  - Ensure no Integrated Security or Trusted Connection params")
