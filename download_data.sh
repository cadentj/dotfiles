mkdir /root/data
mkdir /root/data/sae_chat
mkdir /root/data/sae_diff

huggingface-cli download science-of-finetuning/diffing-stats-SAE-chat-gemma-2-2b-L13-k100-lr1e-04-local-shuffling \
    --repo-type dataset \
    --local-dir /root/data/sae_chat

huggingface-cli download science-of-finetuning/diffing-stats-SAE-difference-gemma-2-2b-L13-k100-lr1e-04-local-shuffling \
    --repo-type dataset \
    --local-dir /root/data/sae_diff