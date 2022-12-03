FROM alpine:3.17
RUN apk add --no-cache bash binutils bison coreutils \
	diffutils findutils gawk gcc grep gzip m4 make \
	patch perl python3 sed tar texinfo xz
