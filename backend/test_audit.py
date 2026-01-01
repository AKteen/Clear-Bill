#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from audit_service import perform_audit
import json

def test_audit_logic():
    """Test the new audit logic with sample data"""
    
    # Sample JSON data from Groq (simulated)
    test_cases = [
        {
            "name": "Approved Invoice",
            "json_data": json.dumps({
                "items": [
                    {"name": "Business Lunch", "category": "Food", "amount": 800.0},
                    {"name": "Office Supplies", "category": "Office Supplies", "amount": 1200.0}
                ],
                "total_amount": 2000.0
            }),
            "groq_response": "Invoice for business expenses"
        },
        {
            "name": "Restricted Items",
            "json_data": json.dumps({
                "items": [
                    {"name": "Wine Bottle", "category": "Alcohol", "amount": 500.0},
                    {"name": "Business Lunch", "category": "Food", "amount": 800.0}
                ],
                "total_amount": 1300.0
            }),
            "groq_response": "Invoice with alcohol purchase"
        },
        {
            "name": "Amount Limit Exceeded",
            "json_data": json.dumps({
                "items": [
                    {"name": "Expensive Dinner", "category": "Food", "amount": 2000.0}
                ],
                "total_amount": 2000.0
            }),
            "groq_response": "Invoice for expensive meal"
        }
    ]
    
    with next(get_db()) as db:
        for test_case in test_cases:
            print(f"\n=== Testing: {test_case['name']} ===")
            
            result = perform_audit(
                test_case['groq_response'], 
                test_case['json_data'], 
                db
            )
            
            print(f"Approval Status: {result.approval_status}")
            print(f"Status Color: {result.status_color}")
            print(f"Compliance Score: {result.compliance_score}%")
            print(f"Summary: {result.summary}")
            print(f"Violations: {len(result.violations)}")
            
            for violation in result.violations:
                print(f"  - {violation['rule_name']}: {violation['message']}")

if __name__ == "__main__":
    test_audit_logic()