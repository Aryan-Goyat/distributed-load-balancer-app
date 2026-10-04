#!/usr/bin/env bash
# Setup git hooks for Linux/macOS
echo "Configuring git hooks directory..."
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
echo "Git hooks enabled! Pre-push test verification is now active."
