export NVM_DIR="$HOME/.nvm"

lazy_load_nvm() {
  unset -f nvm node npm npx pnpm yarn corepack
  [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
  [ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
}

nvm() {
  lazy_load_nvm
  nvm "$@"
}

node() {
  lazy_load_nvm
  node "$@"
}

npm() {
  lazy_load_nvm
  npm "$@"
}

npx() {
  lazy_load_nvm
  npx "$@"
}

pnpm() {
  lazy_load_nvm
  pnpm "$@"
}

yarn() {
  lazy_load_nvm
  yarn "$@"
}

corepack() {
  lazy_load_nvm
  corepack "$@"
}