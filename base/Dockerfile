FROM docker.io/fnndsc/microminc-builder:latest as builder

RUN microminc.sh average_surfaces ray_trace colour_object surface-stats vertstats_stats vertstats_math /microminc

# perl libraries need to be copied manually
# RUN cp -r /opt/CIVET/dist/perl /microminc/perl

FROM python:3.11.2-slim-bullseye
COPY --from=builder /microminc /opt/microminc
ENV PATH=/opt/microminc/bin:$PATH \
    LD_LIBRARY_PATH=/opt/microminc/lib:$LD_LIBRARY_PATH \
    MINC_FORCE_V2=1 MINC_COMPRESS=4 VOLUME_CACHE_THRESHOLD=-1

#    PERL5LIB=/opt/microminc/perl \
