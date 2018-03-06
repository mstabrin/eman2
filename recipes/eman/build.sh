#!/bin/bash

set -xe

env | sort

if [ "${CONDA_BUILD_STATE}" == "BUILD" ];then
    source "${RECIPE_DIR}"/unset_env_vars.sh
fi

build_dir="${SRC_DIR}/../build_eman"

rm -rf $build_dir
mkdir -p $build_dir
cd $build_dir

cmake $SRC_DIR

make -j${CPU_COUNT}
make install
make test-verbose

if [ "$JOB_NAME" != "Centos7" ];then
    if [ "${CONDA_BUILD_STATE}" == "BUILD" ];then
        rm -rfv ${SRC_DIR}/tests/gui/__pycache__
    fi
    make test-gui
fi
