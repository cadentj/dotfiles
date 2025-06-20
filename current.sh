source dotfiles/runpod.sh

# Repos I'm using at the moment
git clone https://github.com/cadentj/autointerp.git
git clone https://github.com/cadentj/steering-finetuning.git

cd /root/autointerp && git checkout dev && uv pip install -e .
cd /root/steering-finetuning && git checkout cleanup && uv pip install -r requirements.txt

uv pip install wandb

wandb login $RUNPOD_WB_TOKEN