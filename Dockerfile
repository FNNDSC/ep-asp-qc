FROM docker.io/fnndsc/pl-surfigures:base-1

LABEL org.opencontainers.image.authors="FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="MNI Surface Figures" \
      org.opencontainers.image.description="A ChRIS plugin to create PNG figures of surfaces and vertex-wise data"

RUN apt-get update && apt-get install -y imagemagick && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/src/pl-surfigures

COPY . .
ARG extras_require=none
RUN pip install ".[${extras_require}]"

CMD ["surfigures"]
