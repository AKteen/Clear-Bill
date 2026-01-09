#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db
from audit_service import perform_audit

def test_image_audit_fallback():
    """Test the fallback keyword detection for images"""
    
    test_cases = [
        {
            "name": "Whiskey Image Response",
            "groq_response": "This invoice shows a purchase of whiskey bottle from ABC Liquor Store for $45.99. The receipt includes tax and shows total amount due.",
            "json_data": "invalid json",  # This will trigger fallback
            "expected_status": "rejected"
        },
        {
            "name": "Wine Bottle Image Response", 
            "groq_response": "Invoice from Wine Shop showing bottle of wine purchase for $25.00. Customer bought red wine for dinner.",
            "json_data": "invalid json",
            "expected_status": "rejected"
        },
        {
            "name": "Alcoholic Beverage Image Response",
            "groq_response": "Receipt shows alcoholic beverage purchase from restaurant. Customer ordered alcoholic drink with meal.",
            "json_data": "invalid json", 
            "expected_status": "rejected"
        },
        {
            "name": "Regular Food Image Response",
            "groq_response": "Invoice from restaurant showing food items: burger, fries, and soda. Total amount $15.50 from McDonald's.",
            "json_data": "invalid json",
            "expected_status": "approved"
        },
        {
            "name": "Entertainment Spa Response",
            "groq_response": "Receipt from luxury spa showing massage services and leisure activities. Total $200 for spa treatment.",
            "json_data": "invalid json",
            "expected_status": "rejected"
        },
        {
            "name": "Luxury Jewelry Response",
            "groq_response": "Invoice from jewelry store showing diamond ring purchase. Luxury item cost $5000 from high-end boutique.",
            "json_data": "invalid json",
            "expected_status": "rejected"
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
            
            print(f"Expected: {test_case['expected_status']}")
            print(f"Actual: {result.approval_status}")
            print(f"Status Color: {result.status_color}")
            print(f"Compliance Score: {result.compliance_score}%")
            print(f"Summary: {result.summary}")
            print(f"Violations: {len(result.violations)}")
            
            for violation in result.violations:
                print(f"  - {violation['rule_name']}: {violation['message']}")
                if 'flagged_items' in violation:
                    print(f"    Flagged: {violation['flagged_items']}")
            
            # Verify result matches expectation
            status_match = result.approval_status == test_case['expected_status']
            print(f"PASS" if status_match else f"FAIL")

if __name__ == "__main__":
    test_image_audit_fallback()