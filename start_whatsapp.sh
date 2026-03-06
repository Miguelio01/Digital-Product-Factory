#!/bin/bash

# S.O.M.A. WhatsApp Orchestrator
# Lanzador de Backend Python + Sidecar Node.js

echo "🚀 Iniciando Ecosistema S.O.M.A. WhatsApp..."

# 1. Iniciar Sidecar de WhatsApp (Node.js) en segundo plano
echo "📦 Iniciando Sidecar de WhatsApp (Puerto 8001)..."
cd whatsapp-service
node index.js &
NODE_PID=$!

# 2. Iniciar Backend S.O.M.A. (Python)
echo "🧠 Iniciando Backend S.O.M.A. (Puerto 8000)..."
cd ../backend
# Asumimos que el venv está activo o usamos el path directo
source venv/bin/activate || echo "⚠️ venv no encontrado, usando python global"
python main.py

# Al cerrar, matar el proceso de Node
trap "kill $NODE_PID" EXIT
