#!/usr/bin/env -S -i /usr/bin/bash
tar -cvf $1.tar *
gzip -v $1.tar
