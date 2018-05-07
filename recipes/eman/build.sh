#!/bin/bash

set -xe

build_dir="${SRC_DIR}/../build_eman"

rm -rf $build_dir
mkdir -p $build_dir
cd $build_dir

if [ "$(uname -s)" == "Darwin" ];then
    LDFLAGS=${LDFLAGS/-Wl,-dead_strip_dylibs/}
fi

if [ "$(uname -s)" == "Linux" ];then
    rm -vf ${CONDA_PREFIX}/include/GL
fi

cmake $SRC_DIR

make -j${CPU_COUNT}
make install

if [ "$(uname -s)" == "Linux" ];then
    rm -v ${CONDA_PREFIX}/include/GL
fi
