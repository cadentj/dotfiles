#!/bin/bash

uv pip install -U "huggingface_hub[cli]"
source /root/.venv/bin/activate
huggingface-cli login # This will prompt for token

apt-get update
apt-get install -y tmux

# Add aliases to bashrc
echo "alias gc='git commit -m'" >> /root/.bashrc
echo "alias tma='tmux attach -t'" >> /root/.bashrc
echo "export HF_HOME=/workspace/hf" >> /root/.bashrc
source /root/.bashrc