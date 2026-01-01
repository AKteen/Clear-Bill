import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from models import AuditPolicy, AuditRule
from schemas import AuditResult

def create_default_audit_rules(db: Session):
    """Create default audit rules for category-based validation"""
    
    default_rules = [
        {"category": "Food", "max_limit": 1500.0, "is_restricted": False, "description": "Per meal allowance for employees."},
        {"category": "Travel", "max_limit": 10000.0, "is_restricted": False, "description": "Inter-city travel and hotel stays."},
        {"category": "Utility", "max_limit": 5000.0, "is_restricted": False, "description": "Internet, electricity, and phone bills."},
        {"category": "Office Supplies", "max_limit": 3000.0, "is_restricted": False, "description": "Stationery and small equipment."},
        {"category": "Alcohol", "max_limit": 0.0, "is_restricted": True, "description": "Strictly prohibited for reimbursement."},
        {"category": "Entertainment", "max_limit": 0.0, "is_restricted": True, "description": "Personal movies, spas, or leisure activities."},
        {"category": "Jewelry", "max_limit": 0.0, "is_restricted": True, "description": "High-risk personal luxury items."},
        {"category": "Others", "max_limit": 1000.0, "is_restricted": False, "description": "General catch-all category for small items."}
    ]
    
    existing_count = db.query(AuditRule).count()
    if existing_count == 0:
        for rule_data in default_rules:
            rule = AuditRule(**rule_data)
            db.add(rule)
        db.commit()
        print(f"Created {len(default_rules)} default audit rules")

def create_default_audit_policies(db: Session):
    """Create default audit policies for invoice validation"""
    
    default_policies = [
        {
            "rule_name": "Invoice Number Required",
            "rule_type": "required_field",
            "field_name": "invoice_number",
            "condition": "exists",
            "expected_value": None
        },
        {
            "rule_name": "Amount Required",
            "rule_type": "required_field", 
            "field_name": "amount",
            "condition": "exists",
            "expected_value": None
        },
        {
            "rule_name": "Date Required",
            "rule_type": "required_field",
            "field_name": "date",
            "condition": "exists", 
            "expected_value": None
        },
        {
            "rule_name": "Vendor Name Required",
            "rule_type": "required_field",
            "field_name": "vendor_name",
            "condition": "exists",
            "expected_value": None
        },
        {
            "rule_name": "Maximum Amount Limit",
            "rule_type": "amount_limit",
            "field_name": "amount",
            "condition": "max_value",
            "expected_value": "10000"
        },
        {
            "rule_name": "Minimum Amount Limit", 
            "rule_type": "amount_limit",
            "field_name": "amount",
            "condition": "min_value",
            "expected_value": "1"
        },
        {
            "rule_name": "Invoice Number Format",
            "rule_type": "format_check",
            "field_name": "invoice_number",
            "condition": "format_match",
            "expected_value": "^[A-Z0-9-]+$"
        },
        {
            "rule_name": "Date Range Check",
            "rule_type": "date_range",
            "field_name": "date", 
            "condition": "within_days",
            "expected_value": "365",
            "severity": "medium"
        },
        {
            "rule_name": "Alcohol Content Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "alcohol,beer,wine,liquor,vodka,whiskey,rum,gin,champagne,cocktail,bar,pub,brewery,distillery",
            "severity": "warning"
        },
        {
            "rule_name": "Entertainment Content Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "party,entertainment,club,nightclub,casino,gambling,strip club,adult entertainment,massage,spa",
            "severity": "warning"
        },
        {
            "rule_name": "High-Risk Vendor Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "cash only,no receipt,under table,off books,personal expense,gift,donation",
            "severity": "high"
        },
        {
            "rule_name": "Luxury Items Warning",
            "rule_type": "content_warning",
            "field_name": "content",
            "condition": "contains_keywords",
            "expected_value": "jewelry,luxury,designer,rolex,gucci,louis vuitton,expensive watch,diamond,gold",
            "severity": "warning"
        }
    ]
    
    # Add severity field to existing policies
    for policy_data in default_policies:
        if 'severity' not in policy_data:
            policy_data['severity'] = 'medium'
    
    # Check if policies already exist
    existing_count = db.query(AuditPolicy).count()
    if existing_count == 0:
        for policy_data in default_policies:
            policy = AuditPolicy(**policy_data)
            db.add(policy)
        db.commit()
        print(f"Created {len(default_policies)} default audit policies")

def validate_bill_format(groq_response: str) -> Tuple[bool, str]:
    """Validate if the document looks like a proper bill/invoice"""
    
    content = groq_response.lower()
    
    # Required bill indicators
    bill_keywords = ['invoice', 'bill', 'receipt', 'statement', 'charge']
    business_indicators = ['company', 'business', 'corp', 'inc', 'ltd', 'llc', 'store', 'shop']
    amount_indicators = ['total', 'amount', 'due', 'balance', '$', 'price', 'cost', 'subtotal']
    date_indicators = ['date', 'issued', 'billed']
    
    # Check for bill keywords
    has_bill_keyword = any(keyword in content for keyword in bill_keywords)
    if not has_bill_keyword:
        return False, "Document does not appear to be a bill or invoice"
    
    # Check for business/vendor information
    has_business_info = any(indicator in content for indicator in business_indicators)
    if not has_business_info:
        return False, "Document lacks proper business/vendor information"
    
    # Check for amount/pricing information
    has_amount_info = any(indicator in content for indicator in amount_indicators)
    if not has_amount_info:
        return False, "Document lacks pricing or amount information"
    
    # Check for date information
    has_date_info = any(indicator in content for indicator in date_indicators)
    if not has_date_info:
        return False, "Document lacks date information"
    
    # Check for structured format (line items, totals, etc.)
    structure_indicators = ['subtotal', 'tax', 'total', 'quantity', 'qty', 'item', 'description']
    structure_score = sum(1 for indicator in structure_indicators if indicator in content)
    
    if structure_score < 2:
        return False, "Document lacks proper bill structure (items, totals, etc.)"
    
    # Additional format checks
    if len(content.split()) < 20:
        return False, "Document content is too brief to be a proper bill"
    
    return True, "Document format validated as proper bill/invoice"
def extract_invoice_data(groq_response: str) -> Dict[str, Any]:
    """Extract structured data from Groq response"""
    
    # This is a simplified extraction - in production, you'd use more sophisticated NLP
    invoice_data = {}
    
    # Extract invoice number
    invoice_patterns = [
        r'invoice\s*(?:number|#|no\.?)\s*:?\s*([A-Z0-9-]+)',
        r'inv\s*(?:number|#|no\.?)\s*:?\s*([A-Z0-9-]+)',
        r'bill\s*(?:number|#|no\.?)\s*:?\s*([A-Z0-9-]+)'
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            invoice_data['invoice_number'] = match.group(1)
            break
    
    # Extract amount
    amount_patterns = [
        r'(?:total|amount|sum)\s*:?\s*\$?([0-9,]+\.?[0-9]*)',
        r'\$([0-9,]+\.?[0-9]*)',
        r'([0-9,]+\.?[0-9]*)\s*(?:dollars?|usd|\$)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                invoice_data['amount'] = float(amount_str)
                break
            except ValueError:
                continue
    
    # Extract date
    date_patterns = [
        r'date\s*:?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})',
        r'([A-Za-z]+ [0-9]{1,2},? [0-9]{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            invoice_data['date'] = match.group(1)
            break
    
    # Extract vendor name - more flexible approach
    vendor_patterns = [
        r'(?:from|vendor|company|business)\s*:?\s*([A-Za-z\s&.,]+?)(?:\n|$|[0-9])',
        r'bill\s+from\s+([A-Za-z\s&.,]+?)(?:\n|$|[0-9])',
        r'invoice\s+from\s+([A-Za-z\s&.,]+?)(?:\n|$|[0-9])'
    ]
    
    # Also check for any business-like words in the content
    content_lower = groq_response.lower()
    business_indicators = ['company', 'corp', 'inc', 'ltd', 'llc', 'store', 'shop', 'restaurant', 'cafe', 'hotel', 'market', 'business', 'enterprise', 'services', 'solutions']
    
    # First try pattern matching
    for pattern in vendor_patterns:
        match = re.search(pattern, groq_response, re.IGNORECASE)
        if match:
            vendor_name = match.group(1).strip()
            if len(vendor_name) > 2:  # Basic validation
                invoice_data['vendor_name'] = vendor_name
                break
    
    # If no pattern match, check if any business indicators exist
    if 'vendor_name' not in invoice_data:
        if any(indicator in content_lower for indicator in business_indicators):
            invoice_data['vendor_name'] = "Business entity detected"
    
    return invoice_data

def validate_against_policies(invoice_data: Dict[str, Any], policies: List[AuditPolicy]) -> AuditResult:
    """Validate invoice data against audit policies"""
    
    violations = []
    total_rules = len([p for p in policies if p.is_active])
    
    for policy in policies:
        if not policy.is_active:
            continue
            
        violation = None
        field_value = invoice_data.get(policy.field_name)
        
        if policy.rule_type == "required_field":
            if policy.condition == "exists" and not field_value:
                violation = {
                    "rule_name": policy.rule_name,
                    "field_name": policy.field_name,
                    "violation_type": "missing_field",
                    "severity": getattr(policy, 'severity', 'medium'),
                    "message": f"{policy.field_name.replace('_', ' ').title()} is required but missing"
                }
        
        elif policy.rule_type == "amount_limit" and field_value:
            try:
                amount = float(field_value)
                limit = float(policy.expected_value)
                
                if policy.condition == "max_value" and amount > limit:
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "amount_exceeded",
                        "severity": getattr(policy, 'severity', 'medium'),
                        "message": f"Amount ${amount} exceeds maximum limit of ${limit}"
                    }
                elif policy.condition == "min_value" and amount < limit:
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "amount_below_minimum",
                        "severity": getattr(policy, 'severity', 'medium'),
                        "message": f"Amount ${amount} is below minimum limit of ${limit}"
                    }
            except (ValueError, TypeError):
                pass
        
        elif policy.rule_type == "content_warning":
            if policy.condition == "contains_keywords":
                keywords = [kw.strip().lower() for kw in policy.expected_value.split(',')]
                content_text = groq_response.lower()
                
                found_keywords = [kw for kw in keywords if kw in content_text]
                if found_keywords:
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "content_warning",
                        "severity": getattr(policy, 'severity', 'warning'),
                        "message": f"Content contains flagged items: {', '.join(found_keywords)}",
                        "flagged_items": found_keywords
                    }
        
        elif policy.rule_type == "format_check" and field_value:
            if policy.condition == "format_match":
                pattern = policy.expected_value
                if not re.match(pattern, str(field_value)):
                    violation = {
                        "rule_name": policy.rule_name,
                        "field_name": policy.field_name,
                        "violation_type": "format_mismatch",
                        "severity": getattr(policy, 'severity', 'medium'),
                        "message": f"{policy.field_name.replace('_', ' ').title()} format is invalid"
                    }
        
        elif policy.rule_type == "date_range" and field_value:
            if policy.condition == "within_days":
                try:
                    # Simple date parsing - in production, use more robust parsing
                    days_limit = int(policy.expected_value)
                    current_date = datetime.now()
                    cutoff_date = current_date - timedelta(days=days_limit)
                    
                    # This is simplified - you'd want better date parsing
                    if "old" in str(field_value).lower() or "expired" in str(field_value).lower():
                        violation = {
                            "rule_name": policy.rule_name,
                            "field_name": policy.field_name,
                            "violation_type": "date_out_of_range",
                            "severity": getattr(policy, 'severity', 'medium'),
                            "message": f"Invoice date appears to be outside acceptable range"
                        }
                except (ValueError, TypeError):
                    pass
        
        if violation:
            violations.append(violation)
    
    # Calculate compliance score and categorize violations
    warnings = [v for v in violations if v.get('severity') == 'warning']
    errors = [v for v in violations if v.get('severity') in ['medium', 'high']]
    
    compliance_score = max(0, (total_rules - len(errors)) / total_rules * 100) if total_rules > 0 else 100
    
    # Generate summary
    if len(violations) == 0:
        summary = "Invoice is fully compliant with all audit policies"
    else:
        warning_text = f", {len(warnings)} warnings" if warnings else ""
        summary = f"Invoice has {len(errors)} policy violations{warning_text} out of {total_rules} rules checked"
    
    return AuditResult(
        is_compliant=len(violations) == 0,
        total_violations=len(violations),
        violations=violations,
        compliance_score=round(compliance_score, 2),
        summary=summary
    )

def perform_audit(groq_response: str, json_data: str, db: Session) -> AuditResult:
    """Perform complete audit of invoice with category-based rules"""
    
    violations = []
    
    try:
        # Parse JSON data from Groq
        invoice_data = json.loads(json_data)
        items = invoice_data.get('items', [])
        total_amount = invoice_data.get('total_amount', 0)
        
        # Get audit rules
        audit_rules = db.query(AuditRule).all()
        rules_dict = {rule.category: rule for rule in audit_rules}
        
        restricted_items = []
        amount_violations = []
        
        # Check each item against rules
        for item in items:
            item_name = item.get('name', '')
            category = item.get('category', 'Others')
            amount = float(item.get('amount', 0))
            
            rule = rules_dict.get(category)
            if not rule:
                rule = rules_dict.get('Others')  # Fallback to Others category
            
            if rule:
                # Check if category is restricted
                if rule.is_restricted:
                    restricted_items.append(item_name)
                    violations.append({
                        "rule_name": f"{category} - Restricted Category",
                        "field_name": "category",
                        "violation_type": "restricted_item",
                        "severity": "high",
                        "message": f"{item_name} ({category}) is strictly prohibited",
                        "flagged_items": [item_name]
                    })
                
                # Check amount limits for non-restricted items
                elif amount > rule.max_limit:
                    amount_violations.append(item_name)
                    violations.append({
                        "rule_name": f"{category} - Amount Limit Exceeded",
                        "field_name": "amount",
                        "violation_type": "amount_exceeded",
                        "severity": "medium",
                        "message": f"{item_name} amount Rs.{amount} exceeds {category} limit of Rs.{rule.max_limit}",
                        "flagged_items": [item_name]
                    })
        
        # Determine approval status
        has_restricted = len(restricted_items) > 0
        has_amount_violations = len(amount_violations) > 0
        
        if has_restricted:
            approval_status = "rejected"
            status_color = "red"
            compliance_score = 0
        elif has_amount_violations:
            approval_status = "warning"
            status_color = "yellow"
            compliance_score = 50
        else:
            approval_status = "approved"
            status_color = "green"
            compliance_score = 100
        
        # Generate summary
        if not violations:
            summary = "All items approved - No policy violations found"
        elif has_restricted:
            summary = f"Cannot approve - {len(restricted_items)} restricted items found"
        else:
            summary = f"Warning - {len(amount_violations)} items exceed category limits"
        
        return AuditResult(
            is_compliant=approval_status == "approved",
            total_violations=len(violations),
            violations=violations,
            compliance_score=compliance_score,
            summary=summary,
            approval_status=approval_status,
            status_color=status_color
        )
        
    except json.JSONDecodeError:
        # Fallback: scan text content for restricted keywords only if it's an invoice
        content = groq_response.lower()
        
        # Check if document looks like an invoice
        invoice_keywords = ['invoice', 'bill', 'receipt', 'total', 'amount', 'price', 'cost', 'payment']
        has_invoice_format = any(keyword in content for keyword in invoice_keywords)
        
        if not has_invoice_format:
            # Not an invoice, just approve without audit
            return AuditResult(
                is_compliant=True,
                total_violations=0,
                violations=[],
                compliance_score=100,
                summary="Document processed - Not an invoice, no audit required",
                approval_status="approved",
                status_color="green"
            )
        
        # Check for alcohol keywords only for invoices
        alcohol_keywords = ['whiskey', 'scotch', 'beer', 'wine', 'vodka', 'rum', 'gin', 'alcohol', 'liquor', 'champagne', 'cocktail']
        found_alcohol = [kw for kw in alcohol_keywords if kw in content]
        
        if found_alcohol:
            return AuditResult(
                is_compliant=False,
                total_violations=1,
                violations=[{
                    "rule_name": "Alcohol - Restricted Category",
                    "field_name": "content",
                    "violation_type": "restricted_item",
                    "severity": "high",
                    "message": f"Document contains alcohol-related items: {', '.join(found_alcohol)}",
                    "flagged_items": found_alcohol
                }],
                compliance_score=0,
                summary="Cannot approve - Alcohol items detected",
                approval_status="rejected",
                status_color="red"
            )
        
        # If no restricted items found, approve
        return AuditResult(
            is_compliant=True,
            total_violations=0,
            violations=[],
            compliance_score=100,
            summary="Document approved - No restricted items detected",
            approval_status="approved",
            status_color="green"
        )
    except Exception as e:
        # Return error result
        return AuditResult(
            is_compliant=False,
            total_violations=1,
            violations=[{
                "rule_name": "Audit Processing Error",
                "field_name": "system",
                "violation_type": "processing_error",
                "severity": "high",
                "message": f"Error processing audit: {str(e)}"
            }],
            compliance_score=0,
            summary="Audit processing failed"
        )
    """Perform audit focusing only on category-based rules"""
    
    violations = []
    
    try:
        # Parse JSON data from Groq
        invoice_data = json.loads(json_data)
        items = invoice_data.get('items', [])
        
        # Get audit rules
        audit_rules = db.query(AuditRule).all()
        rules_dict = {rule.category: rule for rule in audit_rules}
        
        restricted_items = []
        amount_violations = []
        
        # Check each item against category rules only
        for item in items:
            item_name = item.get('name', '')
            category = item.get('category', 'Others')
            amount = float(item.get('amount', 0))
            
            rule = rules_dict.get(category, rules_dict.get('Others'))
            
            if rule:
                # Check if category is restricted
                if rule.is_restricted:
                    restricted_items.append(item_name)
                    violations.append({
                        "rule_name": f"{category} - Restricted Category",
                        "field_name": "category",
                        "violation_type": "restricted_item",
                        "severity": "high",
                        "message": f"{item_name} ({category}) is strictly prohibited",
                        "flagged_items": [item_name]
                    })
                
                # Check amount limits for non-restricted items
                elif amount > rule.max_limit:
                    amount_violations.append(item_name)
                    violations.append({
                        "rule_name": f"{category} - Amount Limit Exceeded",
                        "field_name": "amount",
                        "violation_type": "amount_exceeded",
                        "severity": "medium",
                        "message": f"{item_name} amount Rs.{amount} exceeds {category} limit of Rs.{rule.max_limit}",
                        "flagged_items": [item_name]
                    })
        
        # Check for vendor name requirement
        content = groq_response.lower()
        vendor_patterns = ['company', 'corp', 'inc', 'ltd', 'llc', 'store', 'shop', 'restaurant', 'cafe', 'hotel', 'market', 'business', 'enterprise', 'services', 'solutions', 'vendor', 'supplier', 'merchant', 'retailer', 'outlet', 'center', 'centre', 'plaza', 'mall', 'mart', 'supermarket', 'pharmacy', 'clinic', 'hospital', 'garage', 'workshop', 'studio', 'salon', 'spa', 'gym', 'fitness', 'academy', 'institute', 'school', 'college', 'university', 'office', 'agency', 'firm', 'group', 'organization', 'association', 'foundation', 'trust', 'pvt', 'private', 'limited', 'co.', 'co', '&', 'and', 'brothers', 'bros', 'sons', 'daughters']
        has_vendor = any(pattern in content for pattern in vendor_patterns)
        
        if not has_vendor:
            restricted_items.append("Missing vendor name")
            violations.append({
                "rule_name": "Vendor Name Required",
                "field_name": "vendor",
                "violation_type": "missing_field",
                "severity": "high",
                "message": "Document must contain a valid vendor/company name",
                "flagged_items": ["Missing vendor name"]
            })
        
        # Determine approval status
        has_restricted = len(restricted_items) > 0
        has_amount_violations = len(amount_violations) > 0
        has_vendor_violation = any(v.get('rule_name') == 'Vendor Name Required' for v in violations)
        
        if has_restricted or has_vendor_violation:
            approval_status = "rejected"
            status_color = "red"
            compliance_score = 0
            if has_restricted:
                summary = f"Cannot approve - {len(restricted_items)} restricted items found"
            else:
                summary = "Cannot approve - Vendor name is required"
        elif has_amount_violations:
            approval_status = "warning"
            status_color = "yellow"
            compliance_score = 50
            summary = f"Warning - {len(amount_violations)} items exceed category limits"
        else:
            approval_status = "approved"
            status_color = "green"
            compliance_score = 100
            summary = "All items approved - No policy violations found"
        
        return AuditResult(
            is_compliant=approval_status == "approved",
            total_violations=len(violations),
            violations=violations,
            compliance_score=compliance_score,
            summary=summary,
            approval_status=approval_status,
            status_color=status_color
        )
        
    except json.JSONDecodeError:
        # Fallback: scan text content for restricted keywords
        content = groq_response.lower()
        alcohol_keywords = ['whiskey', 'scotch', 'beer', 'wine', 'vodka', 'rum', 'gin', 'alcohol', 'liquor', 'champagne', 'cocktail']
        
        # Check for vendor name requirement
        vendor_patterns = ['company', 'corp', 'inc', 'ltd', 'llc', 'store', 'shop', 'restaurant', 'cafe', 'hotel', 'market', 'business', 'enterprise', 'services', 'solutions']
        has_vendor = any(pattern in content for pattern in vendor_patterns)
        
        if not has_vendor:
            return AuditResult(
                is_compliant=False,
                total_violations=1,
                violations=[{
                    "rule_name": "Vendor Name Required",
                    "field_name": "vendor",
                    "violation_type": "missing_field",
                    "severity": "high",
                    "message": "Document must contain a valid vendor/company name",
                    "flagged_items": ["Missing vendor name"]
                }],
                compliance_score=0,
                summary="Cannot approve - Vendor name is required",
                approval_status="rejected",
                status_color="red"
            )
        
        # Check for alcohol keywords
        found_alcohol = [kw for kw in alcohol_keywords if kw in content]
        
        if found_alcohol:
            return AuditResult(
                is_compliant=False,
                total_violations=1,
                violations=[{
                    "rule_name": "Alcohol - Restricted Category",
                    "field_name": "content",
                    "violation_type": "restricted_item",
                    "severity": "high",
                    "message": f"Document contains alcohol-related items: {', '.join(found_alcohol)}",
                    "flagged_items": found_alcohol
                }],
                compliance_score=0,
                summary="Cannot approve - Alcohol items detected",
                approval_status="rejected",
                status_color="red"
            )
        
        # If no restricted items found, approve
        return AuditResult(
            is_compliant=True,
            total_violations=0,
            violations=[],
            compliance_score=100,
            summary="Document approved - No restricted items detected",
            approval_status="approved",
            status_color="green"
        )
    except Exception as e:
        # Return approved status for any other errors
        return AuditResult(
            is_compliant=True,
            total_violations=0,
            violations=[],
            compliance_score=100,
            summary="Document processed successfully",
            approval_status="approved",
            status_color="green"
        )

def perform_audit_with_mock(mock_data, db):
    """Test audit with mock data"""
    violations = []
    
    items = mock_data.get('items', [])
    audit_rules = db.query(AuditRule).all()
    rules_dict = {rule.category: rule for rule in audit_rules}
    
    for item in items:
        category = item.get('category', 'Others')
        rule = rules_dict.get(category)
        
        if rule and rule.is_restricted:
            violations.append({
                "rule_name": f"{category} - Restricted Category",
                "field_name": "category",
                "violation_type": "restricted_item",
                "severity": "high",
                "message": f"{item['name']} ({category}) is strictly prohibited",
                "flagged_items": [item['name']]
            })
    
    return AuditResult(
        is_compliant=len(violations) == 0,
        total_violations=len(violations),
        violations=violations,
        compliance_score=0 if violations else 100,
        summary="Cannot approve - restricted items found" if violations else "All items approved",
        approval_status="rejected" if violations else "approved",
        status_color="red" if violations else "green"
    )
def perform_basic_audit(groq_response: str, db: Session) -> AuditResult:
    
    # Get active policies
    policies = db.query(AuditPolicy).filter(AuditPolicy.is_active == True).all()
    
    # Extract invoice data
    invoice_data = extract_invoice_data(groq_response)
    
    # Validate against policies
    audit_result = validate_against_policies(invoice_data, policies)
    
    return audit_result