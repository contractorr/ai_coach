#!/bin/bash
set -e

# Pre-deployment validation script
# Run this before deploying to catch config issues

echo "🔍 Validating deployment configuration..."

# Check docker-compose files exist
for file in docker-compose.yml docker-compose.prod.yml; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing $file"
        exit 1
    fi
done

# Validate syntax (skip if docker not available)
if command -v docker &> /dev/null; then
    echo "✓ Validating docker-compose syntax..."
    docker compose -f docker-compose.yml config > /dev/null
    docker compose -f docker-compose.prod.yml config > /dev/null
else
    echo "⚠️  Skipping docker-compose validation (docker not found)"
fi

# Check critical volume mounts
echo "✓ Checking backend volume mounts..."
for file in docker-compose.yml docker-compose.prod.yml; do
    if ! grep -q "./content:/app/content" "$file"; then
        echo "❌ $file missing curriculum content mount"
        echo "   Backend must include: - ./content:/app/content:ro"
        exit 1
    fi
done

# Check content directory exists
if [ ! -d "content/curriculum" ]; then
    echo "❌ content/curriculum directory not found"
    exit 1
fi

# Count curriculum guides
guide_count=$(find content/curriculum -maxdepth 1 -type d -name "*-guide" | wc -l)
echo "✓ Found $guide_count curriculum guides"

if [ "$guide_count" -lt 30 ]; then
    echo "⚠️  Warning: Expected 40+ guides, found only $guide_count"
fi

# Check required env vars in .env.example
echo "✓ Checking .env.example for required vars..."
required_vars=("SECRET_KEY" "ANTHROPIC_API_KEY" "NEXTAUTH_SECRET" "DOMAIN")
for var in "${required_vars[@]}"; do
    if ! grep -q "^export $var=" .env.example 2>/dev/null && ! grep -q "^$var=" .env.example 2>/dev/null; then
        echo "⚠️  Warning: $var not documented in .env.example"
    fi
done

echo ""
echo "✅ All validation checks passed!"
echo "   Safe to deploy."
