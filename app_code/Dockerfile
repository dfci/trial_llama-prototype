# ai-match-demo/Dockerfile
FROM python:3.12-slim-bullseye

# initialize poetry environment
RUN pip install 'poetry~=1.8' && poetry cache clear pypi --all


# the working
WORKDIR /app

# Define build-time argument
ARG PANEL_PORT

# copy dependencies
COPY pyproject.toml poetry.lock /app/

# create the poetry environment
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi && poetry cache clear pypi --all

# Set environment variable
ENV PANEL_PORT=${PANEL_PORT}
#ENV KUBE_INGRESS_BASE_DOMAIN=${KUBE_INGRESS_BASE_DOMAIN}
#ENV PANEL_PREFIX=${PANEL_PREFIX}
#ENV PANEL_LOG_LEVEL=${PANEL_LOG_LEVEL}

# expose the right port
EXPOSE $PANEL_PORT

# copy app
COPY ai_match_demo /app/
RUN mkdir /app/data

CMD ["sh", "-c", "\
  echo PANEL_PORT=$PANEL_PORT PANEL_PREFIX=$PANEL_PREFIX PANEL_LOG_LEVEL=$PANEL_LOG_LEVEL BASE_DOMAIN=$BASE_DOMAIN WEBSOCKET_ORIGIN=$WEBSOCKET_ORIGIN && \
  panel serve app.py \
  --address 0.0.0.0 \
  --port $PANEL_PORT \
  --prefix $PANEL_PREFIX \
  --log-level $PANEL_LOG_LEVEL \
  --allow-websocket-origin $WEBSOCKET_ORIGIN \
"]