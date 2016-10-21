FROM ubuntu:14.04

MAINTAINER Greg Fitzgerald

RUN apt-get update

RUN apt-get install -y python python-pip python3 && pip install tox

# Dependencies for ruamel.yaml
RUN apt-get install -y python-dev python3-dev

# Dependency for rdflib
RUN apt-get install -y libcurl4-gnutls-dev

COPY . /src

RUN cd /src && tox
