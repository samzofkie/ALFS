FROM alpine:3.17
RUN apk add --no-cache bash binutils bison build-base coreutils \
	diffutils findutils gawk gcc grep gzip m4 make musl-dev\
	patch perl python3 shadow sed tar texinfo xz
WORKDIR /root

#COPY --chown=root *.py ./
#COPY --chown=root build-scripts/ ./build-scripts
#COPY --chown=root .bashrc ./.bashrc
#COPY --chown=root tarball_urls ./tarball_urls
