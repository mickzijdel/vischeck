#!/usr/bin/env bash
set -e

REPO="https://raw.githubusercontent.com/mickzijdel/agent-screenshot/main"
INSTALL_DIR="${SCREENSHOT_INSTALL_DIR:-$HOME/.local/bin}"
HOOKS_DIR="$HOME/.claude/hooks"
SKILLS_DIR="$HOME/.claude/skills/screenshot"

echo "==> Installing screenshot CLI to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
curl -fsSL "$REPO/screenshot" -o "$INSTALL_DIR/screenshot"
chmod +x "$INSTALL_DIR/screenshot"

echo "==> Installing screenshot-reminder hook to $HOOKS_DIR"
mkdir -p "$HOOKS_DIR"
curl -fsSL "$REPO/screenshot-reminder.sh" -o "$HOOKS_DIR/screenshot-reminder.sh"
chmod +x "$HOOKS_DIR/screenshot-reminder.sh"

echo "==> Installing screenshot skill to $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
curl -fsSL "$REPO/skill.md" -o "$SKILLS_DIR/skill.md"

echo ""
echo "Done! Two remaining manual steps:"
echo ""
echo "1. Add the PostToolUse hook to ~/.claude/settings.json"
echo "   (see settings-snippet.json in this repo for the exact entry)"
echo ""
echo "2. Install Playwright if you haven't already:"
echo "   pip install playwright && playwright install chromium"
echo ""
echo "Then add to your project's CLAUDE.md whether it supports dark/light mode, e.g.:"
echo "   ## UI: This app supports dark mode and light mode"
