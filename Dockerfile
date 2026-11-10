# Image de reproduction (CPU). Ollama tourne sur l'hôte ou dans un second conteneur : OLLAMA_HOST.
FROM python:3.11-slim
RUN pip install --no-cache-dir uv==0.5.*
WORKDIR /app
COPY pyproject.toml uv.lock .python-version README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "vigenere_squad.evaluate", "--profil", "small"]
