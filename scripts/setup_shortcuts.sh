#!/bin/bash
# Setup keyboard shortcuts for PyStreamPDF

add_shortcuts() {
  if [ -f ~/.zshrc ]; then
    RC_FILE=~/.zshrc
  elif [ -f ~/.bashrc ]; then
    RC_FILE=~/.bashrc
  else
    echo "❌ No shell config found"; return 1
  fi
  
  if grep -q "dash-pystreampdf" "$RC_FILE"; then
    echo "⚠️  Shortcuts already installed"; return 0
  fi
  
  cat >> "$RC_FILE" << 'ALIASES'

# PyStreamPDF dashboard shortcuts
alias dash-pystreampdf='pystreampdf dashboard --static'
alias dash-pystreampdf-live='pystreampdf dashboard'
alias dash-pystreampdf-export='pystreampdf dashboard --export /tmp/pystreampdf_metrics.json && echo ✓ Exported'
ALIASES
  
  echo "✅ Shortcuts added to $RC_FILE"
  echo "   Run: source $RC_FILE"
}

remove_shortcuts() {
  sed -i '' '/# PyStreamPDF dashboard shortcuts/,/alias dash-pystreampdf-export=/d' ~/.zshrc 2>/dev/null
  sed -i '' '/# PyStreamPDF dashboard shortcuts/,/alias dash-pystreampdf-export=/d' ~/.bashrc 2>/dev/null
  echo "✅ Shortcuts removed"
}

case "${1:-}" in --remove) remove_shortcuts ;; *) add_shortcuts ;; esac
