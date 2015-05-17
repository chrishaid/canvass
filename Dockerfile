# Base Image
FROM ubuntu:latest
MAINTAINER Chris Haid <chaid@kippchicago.org>

# Install dependenciesa
RUN apt-get update
RUN apt-get install -y python
RUN apt-get install -y python-pip
RUN apt-get install -y vim
RUN apt-get install -y git 
RUN pip install Flask

# Update working directories 
ADD . /home/canvass 

WORKDIR /home/canvass