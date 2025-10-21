#!/usr/bin/env bash
set -euo pipefail

# Install build deps
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Fetch llama.cpp
cd commentary
if [ ! -d "llama.cpp" ]; then
  git clone https://github.com/ggerganov/llama.cpp.git
fi
cd llama.cpp
make -j

# Create models dir and instruct user
cd ..
mkdir -p models

echo "======================================================"
echo "llama.cpp built. Now place a Q4 GGUF instruct model at:"
echo "  commentary/models/model.gguf"
echo "Examples: Llama-3.1-8B-Instruct.Q4_K_M.gguf OR Qwen2.5-7B-Instruct.Q4_K_M.gguf"
echo "Download a GGUF and rename to 'model.gguf'."
echo "======================================================"