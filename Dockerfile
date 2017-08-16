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

ADD . /app

ENV HOME ${APP_ROOT}

RUN \
    mv /app/service/* /etc/service && \
    chmod +x /etc/service/*/run

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

WORKDIR /app

RUN pip3 install pipenv && \
    pipenv install --dev --three

RUN rm -rf \
        /root/.cache \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /var/cache/* \
        /usr/include \
        /usr/local/include

RUN chown -R www-data .

EXPOSE ${HTTP_SERVER_PORT}
