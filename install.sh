#!/bin/bash

uv pip install -U "huggingface_hub[cli]"
huggingface-cli login --token $HF_TOKEN