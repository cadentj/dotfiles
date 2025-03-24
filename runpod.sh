#!/bin/bash

# 1) Install uv and create virtual environment
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv python install 3.11
uv venv

# 2) Assuming repo is cloned, run setup scripts
bash dotfiles/setup_github.sh
source dotfiles/install.sh