FROM phusion/baseimage:0.9.19

# Standard stuff
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ARG APP_ROOT /app
ARG HTTP_SERVER_PORT 8080
ARG APP_SERVER_PORT 9000

ENV APP_ROOT {APP_ROOT}
ENV APP_STATIC_ROOT ${APP_ROOT}/static
ENV APPRUN_ROOT ${APP_ROOT}/run
ENV APPRUN_CMD ${APP_ROOT}/bin/steemyo
ENV HTTP_SERVER_PORT ${HTTP_SERVER_PORT}
ENV APP_SERVER_PORT  ${APP_SERVER_PORT}

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
        pandoc

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

# This updates the distro-provided pip and gives us pip3.5 binary
RUN python3.5 -m pip install --upgrade pip

WORKDIR ${APP_ROOT}

# Just enough to build dependencies
COPY ./Pipfile ${APP_ROOT}/Pipfile
COPY ./Makefile ${APP_ROOT}/Makefile

# Install those dependencies
RUN cd ${APP_ROOT} && \
    make requirements.txt && \
    pip3.5 -r requirements.txt

# Copy rest of the code into a suitable place
COPY . ${APP_ROOT}/src
WORKDIR ${APP_ROOT/src

# Build+install yo
RUN cd ${APP_ROOT}/src &&
    make build-without-docker && \
    make install-global

# Setup www-data with a suitable home
WORKDIR ${APPRUN_ROOT}
RUN chown -R www-data:www-data ${APPRUN_ROOT}
USER www-data

# Expose the HTTP server port
EXPOSE {HTTP_SERVER_PORT}
