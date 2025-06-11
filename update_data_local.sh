#!/bin/bash

# Daily Data Update Script - Local Version
# This script replicates the GitHub Actions workflow locally

set -e  # Exit on any error

echo "🚀 Starting Daily Data Update..."
echo "Current directory: $(pwd)"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed"
    exit 1
fi

# Check if query_by_date.py exists
if [ ! -f "query_by_date.py" ]; then
    echo "❌ Error: query_by_date.py not found"
    exit 1
fi

# Check if .env file exists (for environment variables)
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create it with MONGO_URI, MONGO_DB_NAME, and MONGO_COLLECTION_NAME"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "💡 Hint: Activate your virtual environment (mongobgv_query_env) before running this script"
    echo "   Run: source /path/to/mongobgv_query_env/bin/activate"
    echo ""
    echo "🔄 Continuing with system Python..."
else
    echo "✅ Virtual environment detected: $(basename $VIRTUAL_ENV)"
fi

echo "✅ Prerequisites check passed"

# Skip pip install since packages should already be in the virtual environment
echo "📦 Using existing Python environment..."
echo "   Python location: $(which python)"
echo "   Pip location: $(which pip)"

echo "🔍 Running query script..."
# Run the query script (it will use .env file for environment variables)
python query_by_date.py

# Check if data file was generated
echo "📋 Checking if data file was generated..."
if [ -f "data_by_date.json" ]; then
    echo "✅ data_by_date.json exists"
    file_size=$(wc -c < data_by_date.json)
    echo "File size: $file_size bytes"
else
    echo "❌ data_by_date.json was not generated"
    exit 1
fi

# Git operations
echo "📤 Committing and pushing changes..."

# Configure git user (you may want to customize this)
git config --local user.email "$(git config user.email)"
git config --local user.name "$(git config user.name)"

# Add the data file
git add data_by_date.json
# Check if there are changes to commit
echo "Checking for changes..."
if git diff --staged --quiet; then
    echo "🔄 No changes to commit - data is up to date"
else
    echo "📝 Changes detected, committing..."
    commit_message="Update daily data - $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$commit_message"
    
    echo "🚀 Pushing to remote repository..."
    # Check if upstream is set, if not set it
    if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
        echo "Setting upstream branch..."
        git push --set-upstream origin master
    else
        git push
    fi
    echo "✅ Changes committed and pushed successfully"
fi

echo "🎉 Daily data update completed successfully!" 