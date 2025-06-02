#!/bin/bash

# Initialize git repository for AgentiCraft

echo "Initializing git repository..."
git init

echo "Adding remote origin..."
git remote add origin https://github.com/agenticraft/agenticraft.git

echo "Creating initial commit..."
git add .
git commit -m "Initial commit: AgentiCraft framework foundation"

echo "Setting main branch..."
git branch -M main

echo "Git repository initialized successfully!"
echo ""
echo "To push to GitHub, run:"
echo "  git push -u origin main"
echo ""
echo "Current status:"
git status
