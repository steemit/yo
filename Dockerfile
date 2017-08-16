FROM phusion/baseimage:0.9.19

ENV LOG_LEVEL INFO
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV APP_ROOT /app
ENV WSGI_APP ${APP_ROOT}/serve.py
ENV ENVIRONMENT DEV
ENV HTTP_SERVER_PORT 8080
ENV APP_CMD ${APP_ROOT}/yo/serve.py

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
	npm && \
    npm install -g web-push

RUN ln -s "$(which nodejs)" /usr/bin/node

ADD ./service /etc/service

RUN chmod +x /etc/service/*/run

WORKDIR /app

ENV HOME ${APP_ROOT}


# nginx
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

RUN pip3 install pipenv

RUN chown -R www-data ${APP_ROOT}

USER www-data

COPY ./Pipfile /app/Pipfile
COPY ./Pipfile.lock /app/Pipfile.lock
COPY ./scripts /app/scripts
COPY ./html /app/html
COPY ./js /app/js
COPY ./json /app/json
COPY ./yo /app/yo

RUN cd /app && \
    pipenv install --dev --three

USER root

RUN rm -rf \
        /root/.cache \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /var/cache/* \
        /usr/include \
        /usr/local/include


EXPOSE ${HTTP_SERVER_PORT}
