alias venv='source .venv/bin/activate'
alias webserver='python -m http.server'
alias pn=pnpm

# Navigation

alias work="cd $HOME/Programming"

# Tools

export TOOLS_DIR="$HOME/Programming/tools"
alias docs='op run --env-file "$TOOLS_DIR/.env" -- "$TOOLS_DIR/.venv/bin/docs"'