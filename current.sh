source dotfiles/runpod.sh

# Repos I'm using at the moment
git clone https://github.com/ndif-team/nnsight.git
git clone https://github.com/apple/ml-cross-entropy.git
git clone https://github.com/cadentj/autointerp.git
git clone https://github.com/cadentj/OpenRLHF.git
git clone https://github.com/EleutherAI/sparsify.git
git clone https://cadentj:$RUNPOD_GH_TOKEN@github.com/HelenaCasademunt/steering-finetuning.git

cd steering-finetuning && git checkout caden && bash setup.sh
wandb login $RUNPOD_WB_TOKEN