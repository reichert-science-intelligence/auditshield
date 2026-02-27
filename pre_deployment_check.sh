#!/bin/bash
# pre_deployment_check.sh - Verify AuditShield-Live is ready for deployment

set -e

# Change to script directory (auditshield folder)
cd "$(dirname "$0")"

echo "🔍 Pre-Deployment Verification"
echo "=============================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check all required files exist
echo ""
echo "📋 Checking required files..."

files=(
    "Dockerfile:Docker configuration"
    "requirements.txt:Python dependencies"
    "app_complete.py:Main application entry point"
    "app.py:Shiny application"
    "init_complete_system.py:System initialization"
    "database.py:Database manager"
    "database_phase2_schema.py:Phase 2 schema"
    "database_phase3_schema.py:Phase 3 schema"
    "meat_validator.py:AI validation engine"
    "mock_audit_simulator.py:Mock audit simulator"
    "financial_calculator.py:Financial calculator"
    "radv_command_center.py:RADV command center"
    "chart_selection_ai.py:Chart selection AI"
    "education_automation.py:Education automation"
    "realtime_validation.py:Real-time validation"
    "hcc_reconciliation.py:HCC reconciliation"
    "compliance_forecasting.py:Compliance forecasting"
    "regulatory_intelligence.py:Regulatory intelligence"
    "emr_rule_builder.py:EMR rule builder"
    "dashboard_manager.py:Dashboard manager"
    "README.md:HuggingFace README"
    "USER_GUIDE.md:User documentation"
    "DEPLOYMENT_CHECKLIST.md:Deployment guide"
)

missing_count=0

for item in "${files[@]}"; do
    IFS=':' read -r file desc <<< "$item"
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING ($desc)"
        missing_count=$((missing_count + 1))
    fi
done

echo ""
if [ "$missing_count" -eq 0 ]; then
    echo "✅ All required files present"
else
    echo "❌ Missing $missing_count file(s)"
    exit 1
fi

# Test local initialization
echo ""
echo "🧪 Testing local initialization..."
python3 -c "
import sys
errors = []

try:
    from database import get_db_manager
    db = get_db_manager()
    print('  ✅ Database manager imports successfully')
except Exception as e:
    print(f'  ❌ Database manager error: {e}')
    errors.append(str(e))

try:
    from meat_validator import MEATValidator
    validator = MEATValidator()
    print('  ✅ MEATValidator imports successfully')
except Exception as e:
    print(f'  ❌ MEATValidator error: {e}')
    errors.append(str(e))

try:
    from app import app
    print('  ✅ Shiny app imports successfully')
except Exception as e:
    print(f'  ❌ Shiny app error: {e}')
    errors.append(str(e))

if errors:
    sys.exit(1)
print('  ✅ All core modules import successfully')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Local tests failed - fix errors before deploying"
    exit 1
fi

# Check environment variable
echo ""
echo "🔑 Environment variables..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "  ⚠️  ANTHROPIC_API_KEY not set (will need to set in HuggingFace)"
else
    echo "  ✅ ANTHROPIC_API_KEY set"
fi

echo ""
echo "============================================================"
echo "✅ Pre-deployment checks passed!"
echo "============================================================"
echo ""
echo "Ready to deploy. Next steps:"
echo "  1. Run: chmod +x deploy_to_huggingface.sh"
echo "  2. Run: ./deploy_to_huggingface.sh"
echo "  3. Add ANTHROPIC_API_KEY to Space settings"
echo "  4. Wait for build to complete (~10 min)"
echo ""
