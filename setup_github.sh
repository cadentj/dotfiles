#!/bin/bash

# Input arguments
email=${1:-"caden.juang@gmail.com"}
name=${2:-"cadentj"}
github_url=${3:-""}

# 0) Setup git
git config --global user.email "$email"
git config --global user.name "$name"

# Optional: Store credentials
git config --global credential.helper store

# Include the rest of the script someday...
# https://github.com/jplhughes/dotfiles/blob/master/runpod/setup_github.sh