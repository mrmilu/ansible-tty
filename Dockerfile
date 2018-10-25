FROM python:3.6-alpine
LABEL maintainer="aizquierdo@mrmilu.com"

RUN apk update && apk add --no-cache openssh-client sshpass build-base libffi-dev openssl-dev
RUN mkdir /ansible-tty /workdir
COPY . /ansible-tty/
RUN pip install ansible boto
RUN cd /ansible-tty && pip install .
RUN apk del build-base libffi-dev openssl-dev
WORKDIR /workdir

ENTRYPOINT ["ansible-tty"]
