source dotfiles/runpod.sh

# Repos I'm using at the moment
git clone https://github.com/ndif-team/nnsight.git
git clone https://github.com/cadentj/autointerp.git

cd /root/autointerp && git checkout dev && uv pip install -e .

uv pip install wandb

wandb login $RUNPOD_WB_TOKEN