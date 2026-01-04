#!/bin/bash

# 1) Install uv and create virtual environment
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.11
uv venv

# 2) Setup github
bash dotfiles/setup_github.sh

# 3) Install packages
apt-get update
apt-get install -y tmux

# 4) Add aliases
echo "source dotfiles/aliases.sh" >> /root/.bashrc

# 5) Set up environment variables in workspace
echo "export HF_HOME=/workspace/hf" >> /root/.bashrc
echo "export HF_HUB_ENABLE_HF_TRANSFER=1" >> /root/.bashrc

# Reload .bashrc
source /root/.bashrc

# 6) Set up huggingface cache at /workspace/hf
uv pip install -U "huggingface_hub[cli]"
uv pip install -U "huggingface-hub[hf-transfer]"
source /root/.venv/bin/activate

if [ -z "$RUNPOD_HF_TOKEN" ]; then
    huggingface-cli login --add-to-git-credential
else
    huggingface-cli login --token $RUNPOD_HF_TOKEN --add-to-git-credential
fi