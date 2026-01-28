#!/bin/bash

# 1) Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2) Setup github
bash dotfiles/setup_github.sh

# 3) Install packages
apt-get update
apt-get install -y tmux unzip

# 4) Add aliases
echo "source dotfiles/aliases.sh" >> /root/.bashrc