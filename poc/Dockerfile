# =============================================================================
#  Imagem da PoC de ingestao (gerador de carga + sink de metricas)
#  Projeto: Monitoramento de Qualidade do Ar - Atividade 3
# =============================================================================
#  Empacota o pacote qar_poc e os dois entrypoints para que o ambiente ja
#  suba "pronto": o docker-compose usa esta imagem tanto para o sink (sempre
#  observando a ingestao) quanto para o gerador de carga (sob demanda).
# =============================================================================

FROM python:3.12-slim

# Nao gerar .pyc e nao bufferizar a saida (logs aparecem na hora).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependencias primeiro para aproveitar o cache de camadas.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia o pacote e os entrypoints.
COPY qar_poc ./qar_poc
COPY ingestao_teste.py consumidor_metricas.py ./

# Usuario nao-root (boa pratica de container).
RUN useradd --create-home --uid 10001 poc
USER poc

# O comando concreto (sink ou gerador) vem do docker-compose.
ENTRYPOINT ["python"]
CMD ["consumidor_metricas.py", "--help"]
