#!/bin/bash
# Quick verification script for Google ASR configuration

echo "🔍 Google ASR Configuration Verification"
echo "=========================================="
echo ""

# Check .env file
echo "1. Checking .env configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    # Check GOOGLE_APPLICATION_CREDENTIALS
    if grep -q "GOOGLE_APPLICATION_CREDENTIALS=" .env; then
        CREDS_PATH=$(grep "GOOGLE_APPLICATION_CREDENTIALS=" .env | cut -d'=' -f2)
        if [ -f "$CREDS_PATH" ]; then
            echo "   ✅ GOOGLE_APPLICATION_CREDENTIALS is set and file exists"
            echo "      Path: $CREDS_PATH"
        else
            echo "   ❌ GOOGLE_APPLICATION_CREDENTIALS file not found: $CREDS_PATH"
        fi
    else
        echo "   ❌ GOOGLE_APPLICATION_CREDENTIALS not set in .env"
    fi
    
    # Check GOOGLE_CLOUD_PROJECT
    if grep -q "GOOGLE_CLOUD_PROJECT=" .env; then
        PROJECT_ID=$(grep "GOOGLE_CLOUD_PROJECT=" .env | cut -d'=' -f2)
        echo "   ✅ GOOGLE_CLOUD_PROJECT is set: $PROJECT_ID"
    else
        echo "   ❌ GOOGLE_CLOUD_PROJECT not set in .env"
    fi
    
    # Check GCS_BUCKET_NAME
    if grep -q "GCS_BUCKET_NAME=" .env; then
        BUCKET=$(grep "GCS_BUCKET_NAME=" .env | cut -d'=' -f2)
        echo "   ✅ GCS_BUCKET_NAME is set: $BUCKET"
    else
        echo "   ❌ GCS_BUCKET_NAME not set in .env"
    fi
else
    echo "   ❌ .env file not found"
fi

echo ""
echo "2. Testing provider initialization..."
python3 test_google_providers.py

echo ""
echo "=========================================="
echo "Verification complete!"
echo ""
echo "To test with the API server:"
echo "  1. Run: ./start_experiments.sh"
echo "  2. Open: http://localhost:8000/experiments.html"
echo "  3. Select Google providers and upload audio"
echo ""
