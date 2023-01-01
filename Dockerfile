FROM alpine:3.17
RUN apk add --no-cache bash binutils bison coreutils \
	diffutils findutils gawk gcc grep gzip m4 make musl-dev\
	patch perl python3 shadow sed tar texinfo xz

# Create lfs user and group
RUN groupadd lfs
RUN useradd -s /bin/bash -g lfs -m -k /dev/null lfs
USER lfs

# Switch to working dir
WORKDIR /home/lfs

# Copy Python script
#COPY --chown=lfs:lfs ./build_cross_compiler.py .
#RUN ./build_cross_compiler.py

