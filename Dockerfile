FROM python:3

ENV PYTHONUNBUFFERED 1
ENV PKG_DIR /tmp/pkg
ENV SRC_DIR /tmp/src

RUN apt-get update && apt install -y vim
#COPY pkg/*.txt ${PKG_DIR}/
RUN pip install --upgrade pip && \
    pip install --upgrade spaceone-api&& \
    pip install --upgrade spaceone-core

COPY src ${SRC_DIR}

ARG CACHEBUST=1
WORKDIR ${SRC_DIR}
RUN python3 setup.py install && \
    rm -rf /tmp/*

WORKDIR /opt
ENTRYPOINT ["spaceone"]
CMD ["test"]