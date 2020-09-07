FROM ubuntu:20.04

ENV DEBIAN_FRONTEND "noninteractive"
ENV TZ="America/Los_Angeles"

RUN apt-get update -y && apt-get install -y tzdata python3 python3-pip git unzip curl

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
        && unzip awscliv2.zip \
        && ./aws/install \
        && rm awscliv2.zip \
        && rm -fr aws


COPY requirements.txt /
RUN pip3 install -r /requirements.txt && rm /requirements.txt

RUN apt-get install -y cargo \
	&& cargo install tokei
ENV PATH $PATH:/root/.cargo/bin

COPY semgrepl /root/semgrepl
COPY rules /root/rules
COPY batch.sh /root

WORKDIR /root

