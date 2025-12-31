FROM docker.n8n.io/n8nio/n8n:latest

USER root

# Install AI CLI tools
RUN npm install -g @google/gemini-cli@latest
RUN npm install -g @openai/codex@latest

USER node
