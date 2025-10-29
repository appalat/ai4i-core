#!/usr/bin/env python3
"""
Verification script to check seed data accuracy in service registry.
Compares SQL seed file, Python seed script, and optionally database state.
"""

import json
import re
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
SQL_SEED_FILE = BASE_DIR / "infrastructure" / "postgres" / "09-config-seed-data.sql"
PYTHON_SEED_FILE = BASE_DIR / "services" / "config-service" / "seed_services.py"


def extract_sql_seed_data(sql_file: Path) -> Dict[str, Dict[str, Any]]:
    """Extract service registry data from SQL seed file."""
    if not sql_file.exists():
        print(f"❌ SQL seed file not found: {sql_file}")
        return {}
    
    services = {}
    
    with open(sql_file, 'r') as f:
        content = f.read()
    
    # Find service registry INSERT statement
    # Pattern: INSERT INTO service_registry (service_name, service_url, health_check_url, status, metadata) VALUES
    pattern = r"INSERT INTO service_registry.*?VALUES\s*(.*?)\s*ON CONFLICT"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("⚠️  Could not find service_registry INSERT statement in SQL file")
        return services
    
    values_block = match.group(1)
    
    # Parse each service entry
    # Format: ('service-name', 'url', 'health-url', 'status', '{"metadata": "json"}')
    # More robust pattern that handles multi-line and escaped quotes
    service_pattern = r"\('([^']+)',\s*'([^']+)',\s*'([^']*)',\s*'([^']+)',\s*'({(?:[^'}]|'[^']*')*})'\)"
    
    for match in re.finditer(service_pattern, values_block, re.DOTALL):
        service_name = match.group(1)
        service_url = match.group(2)
        health_check_url = match.group(3)
        status = match.group(4)
        metadata_str = match.group(5)
        
        try:
            # Clean up metadata JSON string
            # Replace single quotes with double quotes for JSON
            # But be careful with quotes inside strings
            # Simple approach: replace 'key': with "key": and 'value' with "value"
            metadata_str = re.sub(r"'([^']+)':\s*", r'"\1": ', metadata_str)  # Replace 'key': with "key":
            metadata_str = re.sub(r":\s*'([^']+)'", r': "\1"', metadata_str)  # Replace : 'value' with : "value"
            metadata_str = re.sub(r":\s*\[([^\]]+)\]", lambda m: ': [' + re.sub(r"'([^']+)'", r'"\1"', m.group(1)) + ']', metadata_str)  # Handle arrays
            
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError as e:
            print(f"⚠️  Error parsing metadata for {service_name}: {e}")
            print(f"   Metadata string: {metadata_str[:100]}...")
            metadata = {}
        
        services[service_name] = {
            "service_name": service_name,
            "service_url": service_url,
            "health_check_url": health_check_url,
            "status": status,
            "metadata": metadata
        }
    
    return services


def extract_python_seed_data(python_file: Path) -> Dict[str, Dict[str, Any]]:
    """Extract service registry data from Python seed script."""
    if not python_file.exists():
        print(f"❌ Python seed file not found: {python_file}")
        return {}
    
    services = {}
    
    try:
        # Use importlib to import the SERVICES list directly
        import importlib.util
        import sys
        
        # Create a unique module name to avoid conflicts
        module_name = f"seed_services_{id(python_file)}"
        spec = importlib.util.spec_from_file_location(module_name, python_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {python_file}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # Register to avoid re-import issues
        spec.loader.exec_module(module)
        
        # Extract SERVICES list
        if not hasattr(module, 'SERVICES'):
            print("⚠️  SERVICES variable not found in Python file")
            return services
        
        for service in module.SERVICES:
            service_name = service.get('service_name')
            if service_name:
                services[service_name] = {
                    "service_name": service_name,
                    "service_url": service.get('service_url', ''),
                    "health_check_url": service.get('health_check_url', ''),
                    "status": "unknown",  # Default in Python script
                    "metadata": service.get('metadata', {})
                }
        
        # Clean up
        del sys.modules[module_name]
        
    except Exception as e:
        print(f"❌ Error importing Python module: {e}")
        import traceback
        traceback.print_exc()
    
    return services


def compare_data(
    sql_data: Dict[str, Dict[str, Any]],
    python_data: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Compare SQL and Python seed data and return discrepancies."""
    all_services = set(sql_data.keys()) | set(python_data.keys())
    
    discrepancies = {
        "missing_in_python": [],
        "missing_in_sql": [],
        "field_mismatches": []
    }
    
    for service_name in all_services:
        sql_service = sql_data.get(service_name)
        python_service = python_data.get(service_name)
        
        if not sql_service:
            discrepancies["missing_in_sql"].append(service_name)
            continue
        
        if not python_service:
            discrepancies["missing_in_python"].append(service_name)
            continue
        
        # Compare fields
        mismatches = []
        
        # Compare service_url
        if sql_service["service_url"] != python_service["service_url"]:
            mismatches.append({
                "field": "service_url",
                "sql": sql_service["service_url"],
                "python": python_service["service_url"]
            })
        
        # Compare health_check_url
        if sql_service["health_check_url"] != python_service["health_check_url"]:
            mismatches.append({
                "field": "health_check_url",
                "sql": sql_service["health_check_url"],
                "python": python_service["health_check_url"]
            })
        
        # Compare metadata (deep comparison)
        sql_metadata = sql_service.get("metadata", {})
        python_metadata = python_service.get("metadata", {})
        
        # Compare key metadata fields
        metadata_fields = ["version", "environment", "description", "port", "type", "capabilities"]
        for field in metadata_fields:
            sql_val = sql_metadata.get(field)
            python_val = python_metadata.get(field)
            
            # Handle list comparison
            if isinstance(sql_val, list) and isinstance(python_val, list):
                if sorted(sql_val) != sorted(python_val):
                    mismatches.append({
                        "field": f"metadata.{field}",
                        "sql": sql_val,
                        "python": python_val
                    })
            elif sql_val != python_val:
                mismatches.append({
                    "field": f"metadata.{field}",
                    "sql": sql_val,
                    "python": python_val
                })
        
        if mismatches:
            discrepancies["field_mismatches"].append({
                "service_name": service_name,
                "mismatches": mismatches
            })
    
    return discrepancies


def print_comparison_report(
    sql_data: Dict[str, Dict[str, Any]],
    python_data: Dict[str, Dict[str, Any]],
    discrepancies: Dict[str, Any]
):
    """Print a detailed comparison report."""
    print("=" * 80)
    print("SERVICE REGISTRY SEED DATA VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    print(f"SQL Seed File: {SQL_SEED_FILE}")
    print(f"Python Seed File: {PYTHON_SEED_FILE}")
    print()
    
    print(f"📊 Summary:")
    print(f"   Services in SQL seed: {len(sql_data)}")
    print(f"   Services in Python seed: {len(python_data)}")
    print()
    
    # Check for missing services
    if discrepancies["missing_in_python"]:
        print(f"❌ Services missing in Python seed ({len(discrepancies['missing_in_python'])}):")
        for service in discrepancies["missing_in_python"]:
            print(f"   • {service}")
        print()
    
    if discrepancies["missing_in_sql"]:
        print(f"❌ Services missing in SQL seed ({len(discrepancies['missing_in_sql'])}):")
        for service in discrepancies["missing_in_sql"]:
            print(f"   • {service}")
        print()
    
    # Check for field mismatches
    if discrepancies["field_mismatches"]:
        print(f"⚠️  Field Mismatches ({len(discrepancies['field_mismatches'])}):")
        for item in discrepancies["field_mismatches"]:
            print(f"\n   Service: {item['service_name']}")
            for mismatch in item["mismatches"]:
                print(f"      Field: {mismatch['field']}")
                print(f"         SQL:    {mismatch['sql']}")
                print(f"         Python: {mismatch['python']}")
        print()
    
    # If no discrepancies, show success
    total_issues = (
        len(discrepancies["missing_in_python"]) +
        len(discrepancies["missing_in_sql"]) +
        len(discrepancies["field_mismatches"])
    )
    
    if total_issues == 0:
        print("✅ All seed data sources match perfectly!")
        print()
        print("Registered Services:")
        for service_name in sorted(sql_data.keys()):
            service = sql_data[service_name]
            metadata = service.get("metadata", {})
            print(f"   • {service_name:30s} | {metadata.get('type', 'N/A'):10s} | {service['service_url']}")
    else:
        print(f"⚠️  Found {total_issues} discrepancy(ies) - review above for details")
    
    print()
    print("=" * 80)


def query_database() -> Optional[Dict[str, Dict[str, Any]]]:
    """Optional: Query the actual database to verify current state."""
    try:
        import os
        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import select
        
        # Try to get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("⚠️  DATABASE_URL not set - skipping database verification")
            return None
        
        # Import the model (we'll need to add parent to path)
        sys.path.insert(0, str(Path(__file__).parent))
        from models.database_models import ServiceRegistryDB
        
        async def fetch_services():
            engine = create_async_engine(database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                result = await session.execute(select(ServiceRegistryDB))
                services = result.scalars().all()
                
                db_services = {}
                for service in services:
                    db_services[service.service_name] = {
                        "service_name": service.service_name,
                        "service_url": service.service_url,
                        "health_check_url": service.health_check_url or "",
                        "status": service.status,
                        "metadata": service.service_metadata or {}
                    }
                
                await engine.dispose()
                return db_services
        
        return asyncio.run(fetch_services())
    
    except ImportError as e:
        print(f"⚠️  Could not import required modules for database query: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Error querying database: {e}")
        return None


def main():
    """Main verification function."""
    print("🔍 Extracting service registry data from seed files...")
    print()
    
    # Extract data from both sources
    sql_data = extract_sql_seed_data(SQL_SEED_FILE)
    python_data = extract_python_seed_data(PYTHON_SEED_FILE)
    
    if not sql_data and not python_data:
        print("❌ Could not extract data from either seed file")
        sys.exit(1)
    
    # Compare SQL vs Python seed data
    discrepancies = compare_data(sql_data, python_data)
    
    # Print report
    print_comparison_report(sql_data, python_data, discrepancies)
    
    # Optionally query database
    print("\n" + "=" * 80)
    print("OPTIONAL: Database Verification")
    print("=" * 80)
    db_data = query_database()
    
    if db_data:
        print(f"\n📊 Database State:")
        print(f"   Services in database: {len(db_data)}")
        
        # Compare database with seed data (use SQL as reference)
        db_discrepancies = compare_data(sql_data, db_data)
        
        if (len(db_discrepancies["missing_in_sql"]) == 0 and 
            len(db_discrepancies["missing_in_python"]) == 0 and 
            len(db_discrepancies["field_mismatches"]) == 0):
            print("✅ Database data matches seed data!")
        else:
            print("\n⚠️  Database discrepancies found:")
            if db_discrepancies["missing_in_python"]:
                print(f"   Services in seed but not in DB: {db_discrepancies['missing_in_python']}")
            if db_discrepancies["missing_in_sql"]:
                print(f"   Services in DB but not in seed: {db_discrepancies['missing_in_sql']}")
            if db_discrepancies["field_mismatches"]:
                print(f"   Field mismatches: {len(db_discrepancies['field_mismatches'])} services")
                for item in db_discrepancies["field_mismatches"][:5]:  # Show first 5
                    print(f"      • {item['service_name']}: {[m['field'] for m in item['mismatches']]}")
    else:
        print("\n💡 To verify database state, set DATABASE_URL environment variable")
        print("   Example: export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/config_db")
    
    # Exit with appropriate code
    total_issues = (
        len(discrepancies["missing_in_python"]) +
        len(discrepancies["missing_in_sql"]) +
        len(discrepancies["field_mismatches"])
    )
    
    if total_issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

