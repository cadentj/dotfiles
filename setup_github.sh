#!/bin/bash

apt-get update
apt-get install -y gh

# Input arguments
email=${1:-"caden.juang@gmail.com"}
name=${2:-"cadentj"}
github_url=${3:-""}

# Setup git
git config --global user.email "$email"
git config --global user.name "$name"

# Optional: Store credentials
git config --global credential.helper store

# Set GitHub token for GitHub CLI
echo $RUNPOD_GH_TOKEN | gh auth login --with-token