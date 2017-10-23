FROM phusion/baseimage:0.9.19

# Standard stuff
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ARG SOURCE_COMMIT
ENV SOURCE_COMMIT ${SOURCE_COMMIT}
ARG DOCKER_TAG
ENV DOCKER_TAG ${DOCKER_TAG}

ENV HTTP_SERVER_PORT 8080
ENV APP_SERVER_PORT 9000

ENV APP_ROOT /app
ENV APP_STATIC_ROOT ${APP_ROOT}/static
ENV APPRUN_ROOT ${APP_ROOT}
ENV APPRUN_CMD ${APP_ROOT}/bin/steemyo

ENV ENVIRONMENT DEV

# Dependencies
RUN \
    apt-get update && \
    apt-get install -y \
        build-essential \
        daemontools \
        git \
        libffi-dev \
        libmysqlclient-dev \
        libssl-dev \
        make \
        python3 \   
        python3-dev \
        python3-pip \
        libxml2-dev \
        libxslt-dev \
        runit \
        nginx \
        nodejs \
        wget \
        libsqlite3-dev \
        pandoc

# Python 3.6
RUN \
    wget https://www.python.org/ftp/python/3.6.2/Python-3.6.2.tar.xz && \
    tar xvf Python-3.6.2.tar.xz && \
    cd Python-3.6.2/ && \
    ./configure && \
    make altinstall

# Configure nginx etc

RUN \
  mkdir -p /var/lib/nginx/body && \
  mkdir -p /var/lib/nginx/scgi && \
  mkdir -p /var/lib/nginx/uwsgi && \
  mkdir -p /var/lib/nginx/fastcgi && \
  mkdir -p /var/lib/nginx/proxy && \
  chown -R www-data:www-data /var/lib/nginx && \
  mkdir -p /var/log/nginx && \
  touch /var/log/nginx/access.log && \
  touch /var/log/nginx/error.log && \
  chown www-data:www-data /var/log/nginx/*.log && \
  touch /var/run/nginx.pid && \
  chown www-data:www-data /var/run/nginx.pid


ADD ./service /etc/service
RUN chmod +x /etc/service/*/run

# This updates the distro-provided pip and gives us pip3.6 binary
RUN python3.6 -m pip install --upgrade pip


# Install PipEnv
RUN pip3.6 install pipenv

WORKDIR ${APP_ROOT}

# Copy code into a suitable place
COPY ./bin ${APP_ROOT}/bin
COPY ./data ${APP_ROOT}/data
COPY ./Makefile ${APP_ROOT}/Makefile
COPY ./package_meta.py ${APP_ROOT}/package_meta.py
COPY ./Pipfile ${APP_ROOT}/Pipfile
COPY ./scripts ${APP_ROOT}/scripts
COPY ./setup.cfg ${APP_ROOT}/setup.cfg
COPY ./setup.py ${APP_ROOT}/setup.py
COPY ./tests ${APP_ROOT}/tests
COPY ./yo ${APP_ROOT}/yo
COPY ./yo.cfg ${APP_ROOT}/yo.cfg

# More deps

RUN apt-get -y install dh-autoreconf pkg-config
RUN git clone https://github.com/bitcoin-core/secp256k1.git && \
    cd secp256k1 && \
    ./autogen.sh && \
    ./configure && \
    make all install

# Build+install yo
RUN make Pipfile.lock && \
    make build-without-docker && \
    make install-pipenv

# let the test suite know it's inside docker
ENV INDOCKER 1

# Expose the HTTP server port
EXPOSE ${HTTP_SERVER_PORT}
