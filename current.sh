# Repos I'm using at the moment
# git clone https://github.com/ndif-team/nnsight.git
# git clone https://github.com/apple/ml-cross-entropy.git
# git clone https://github.com/cadentj/autointerp.git
# git clone https://github.com/cadentj/OpenRLHF.git
# git clone https://github.com/saprmarks/dictionary_learning.git
# echo "cadentj\n$RUNPOD_GH_TOKEN" | git clone https://github.com/HelenaCasademunt/steering-finetuning.git
# git clone https://cadentj:$RUNPOD_GH_TOKEN@github.com/HelenaCasademunt/steering-finetuning.git
echo $RUNPOD_GH_TOKEN

git clone https://oauth2:$RUNPOD_GH_TOKEN@github.com/HelenaCasademunt/steering-finetuning.git
# cd steering-finetuning && git checkout caden && bash setup.sh
# wandb login $RUNPOD_WB_TOKEN