FROM ubuntu
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y bash binutils bison coreutils diffutils findutils file \
  gawk gcc g++ gzip m4 make patch perl python3 sed tar texinfo xz-utils
WORKDIR /root
