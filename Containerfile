ARG PYTHON_VERSION=3.10.5
FROM python:${PYTHON_VERSION}-slim-bullseye as base

ARG WKHTMLTOPDF_VERSION=0.12.6-1
ARG NODE_VERSION=16.18.0
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN useradd -ms /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    git \
    vim \
    nginx \
    gettext-base \
    # MariaDB
    mariadb-client \
    # Postgres
    libpq-dev \
    postgresql-client \
    # For healthcheck
    wait-for-it \
    jq \
    # NodeJS
    && mkdir -p ${NVM_DIR} \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.2/install.sh | bash \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >>/home/frappe/.bashrc \
    # Install wkhtmltopdf with patched qt
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_$WKHTMLTOPDF_VERSION.buster_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && rm -fr /etc/nginx/sites-enabled/default \
    && pip3 install frappe-bench

FROM base as builder

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    # For frappe framework
    wget \
    # For psycopg2
    libpq-dev \
    # Other
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    cron \
    # For pandas
    gcc \
    build-essential \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

USER frappe

ARG FRAPPE_BRANCH=version-14
ARG FRAPPE_PATH=https://github.com/frappe/frappe
RUN bench init \
  --frappe-branch=${FRAPPE_BRANCH} \
  --frappe-path=${FRAPPE_PATH} \
  --no-procfile \
  --no-backups \
  --skip-redis-config-generation \
  --verbose \
  --skip-assets \
  /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

# Place all your apps including ERPNext in repos directory
COPY --chown=frappe:frappe repos apps

RUN bench setup requirements
RUN bench build --production --verbose --hard-link

FROM base as backend

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench
COPY resources/gevent_patch.py /opt/patches/
COPY resources/nginx-template.conf /templates/nginx/frappe.conf.template
COPY resources/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh

# Fixes for non-root nginx and logs to stdout
RUN chown -R frappe:frappe /var/lib/nginx && \
  chown -R frappe:frappe /var/log/nginx && \
  chown -R frappe:frappe /etc/nginx/conf.d && \
  chown -R frappe:frappe /etc/nginx/nginx.conf && \
  sed -i '/user www-data/d' /etc/nginx/nginx.conf && \
  ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log && \
  touch /var/run/nginx.pid && \
  chown -R frappe:frappe /var/run/nginx.pid

USER frappe
WORKDIR /home/frappe/frappe-bench/sites

VOLUME [ \
  "/home/frappe/frappe-bench/sites", \
  "/home/frappe/frappe-bench/logs", \
  "/home/frappe/frappe-bench/sites/assets", \
  "/home/frappe/frappe-bench/apps", \
  "/home/frappe/frappe-bench/env" \
]

CMD [ \
  "/home/frappe/frappe-bench/env/bin/gunicorn", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "--worker-class=gthread", \
  "--worker-tmp-dir=/dev/shm", \
  "--timeout=120", \
  "--preload", \
  "frappe.app:application" \
]
