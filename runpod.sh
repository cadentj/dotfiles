#!/bin/bash

DEFAULT_KEY="runpod_mats"

# 1) Get key name and SSH command from arguments and connect to Pod
if [ $# -lt 1 ]; then
    echo "Usage: $0 [key_name] <ssh_command>"
    exit 1
fi

# If first argument is the SSH command (no key name provided), use default key
if [[ "$1" == *"ssh"* ]]; then
    key_name="$DEFAULT_KEY"
    ssh_command="$@"
else
    key_name="$1"  # Get the key name from first argument
    shift  # Remove the first argument, leaving only the SSH command
    ssh_command="$@"
fi

# Extract host, port from SSH command
host=$(echo "$ssh_command" | grep -o '@[0-9.]*' | cut -d'@' -f2)
port=$(echo "$ssh_command" | grep -o '\-p [0-9]*' | cut -d' ' -f2)

# Add to SSH config if host and port were found
if [ ! -z "$host" ] && [ ! -z "$port" ]; then
    config_entry="\nHost $host
  HostName $host
  User root
  Port $port
  IdentityFile ~/.ssh/$key_name"
    
    # Add to ~/.ssh/config, avoiding duplicates
    if ! grep -q "Host $host" ~/.ssh/config; then
        echo -e "\n$config_entry" >> ~/.ssh/config
    fi
fi

# 2) Run setup script with variables
temp_script=$(mktemp)
cat > "$temp_script" << 'EOF'
# Install uv and create virtual environment
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.11
uv venv

# Setup dotfiles
mkdir -p git && cd git
git clone https://github.com/cadentj/dotfiles.git
cd dotfiles
bash setup_github.sh
bash setup_aliases.sh
bash install.sh
EOF

# Combine SSH command with script
modified_command="${ssh_command/id_ed25519/$key_name} -o StrictHostKeyChecking=no 'bash -s' < ${temp_script}"
eval "$modified_command"

echo $modified_command

# Clean up
rm "$temp_script"