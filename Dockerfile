FROM jfear/centos7-miniconda3:py3.5

MAINTAINER Justin Fear <justin.m.fear@gmail.com>

RUN conda install -y biometalib

CMD ["/bin/bash"]
