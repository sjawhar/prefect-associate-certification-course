# syntax=docker/dockerfile:1.6.0-labs
ARG PYTHON_VERSION=3.11.8-bookworm
FROM python:${PYTHON_VERSION} AS packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        bash-completion \
        jq \
        nano \
        rsync \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN pip install \
    --no-cache-dir \
    pip==24.0 \
    poetry==1.7.1

WORKDIR /usr/src
COPY pyproject.toml poetry.lock ./
RUN POETRY_VIRTUALENVS_IN_PROJECT=true \
    poetry install --no-root
ENV PATH=/usr/src/.venv/bin:${PATH}

ARG USERNAME=prefect
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd -g ${USER_GID} ${USERNAME} \
 && useradd -m -u ${USER_UID} -g ${USER_GID} -s /bin/bash ${USERNAME} \
 && mkdir -p /home/${USERNAME}/app \
 && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}

WORKDIR /home/${USERNAME}/app
COPY . .
RUN . /usr/src/.venv/bin/activate \
 && poetry install --no-cache

USER ${USERNAME}
