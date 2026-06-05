#!/bin/bash
# 等待 Ollama 服务启动，然后拉取指定模型
set -e

MODEL="${OLLAMA_MODEL:-deepseek-r1:7b}"

echo "⏳ 等待 Ollama 服务就绪..."
until ollama list > /dev/null 2>&1; do
  sleep 2
done

echo "📥 拉取模型: $MODEL"
ollama pull "$MODEL"
echo "✅ 模型 $MODEL 已就绪"
