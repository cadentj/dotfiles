#!/bin/bash

# 1) Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2) Setup github
bash dotfiles/setup_github.sh

# 3) Install packages
apt-get update
apt-get install -y vim tmux unzip

# 4) Add alias to .bashrc in root
echo "source /root/dotfiles/aliases.sh" >> /root/.bashrc
