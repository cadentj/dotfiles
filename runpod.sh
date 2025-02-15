#!/bin/bash

# 1) Get key name and SSH command from arguments and connect to Pod
if [ $# -lt 1 ]; then
    echo "Usage: $0 <key_name> <ssh_command>"
    exit 1
fi
key_name="$1"  # Get the key name from first argument
shift  # Remove the first argument, leaving only the SSH command
ssh_command="$@"
modified_command="${ssh_command/id_ed25519/$key_name}"
eval "$modified_command"

# 2) Install uv and create virtual environment
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.11
uv venv 

# 3) Setup dotfiles
mkdir git && cd git
git clone https://github.com/cadentj/dotfiles.git
cd dotfiles
bash setup_github.sh