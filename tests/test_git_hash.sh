#!/usr/bin/env bash

set -xe

VER=$(python -c "from EMAN2_meta import GITHASH as ver; print(ver)")
test "$VER" == "$GIT_COMMIT_SHORT"
