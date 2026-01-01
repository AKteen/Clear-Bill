#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine, get_db
from models import Base, AuditRule
from audit_service import create_default_audit_rules

def migrate_audit_rules():
    """Add audit_rules table and populate with default data"""
    
    try:
        # Create the audit_rules table
        print("Creating audit_rules table...")
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] audit_rules table created successfully")
        
        # Initialize default audit rules
        print("Initializing default audit rules...")
        with next(get_db()) as db:
            create_default_audit_rules(db)
        print("[SUCCESS] Default audit rules initialized")
        
        print("[COMPLETE] Migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    migrate_audit_rules()