#!/bin/bash

echo "======================================"
echo "GitHub Repository Setup Helper"
echo "======================================"
echo ""
echo "This script will help you push your code to GitHub."
echo ""
echo "Prerequisites:"
echo "1. You have a GitHub account"
echo "2. You are logged in to GitHub in your browser"
echo ""
echo "Steps:"
echo ""
echo "STEP 1: Create a new repository on GitHub"
echo "  - Go to: https://github.com/new"
echo "  - Repository name: document-search-service"
echo "  - Description: Distributed Document Search Service - Technical Assessment"
echo "  - Visibility: Public (or Private if you prefer)"
echo "  - DO NOT initialize with README, .gitignore, or license"
echo "  - Click 'Create repository'"
echo ""
echo "STEP 2: Copy your repository URL from GitHub"
echo "  Example: https://github.com/YOUR-USERNAME/document-search-service.git"
echo ""
read -p "Enter your repository URL: " REPO_URL
echo ""

if [ -z "$REPO_URL" ]; then
    echo "Error: Repository URL cannot be empty"
    exit 1
fi

echo "======================================"
echo "Pushing code to GitHub..."
echo "======================================"
echo ""

# Add remote
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

# Push to GitHub
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ SUCCESS!"
    echo "======================================"
    echo ""
    echo "Your code has been pushed to GitHub!"
    echo ""
    echo "Repository URL: $REPO_URL"
    echo ""
    echo "Next steps:"
    echo "1. Open your repository in browser to verify"
    echo "2. Check that README displays correctly"
    echo "3. Use this URL in your submission email"
    echo ""
else
    echo ""
    echo "======================================"
    echo "❌ ERROR"
    echo "======================================"
    echo ""
    echo "Failed to push to GitHub. Common issues:"
    echo "1. Invalid repository URL"
    echo "2. Not authenticated with GitHub"
    echo "3. Repository doesn't exist"
    echo ""
    echo "Please check the URL and try again."
    echo ""
fi
