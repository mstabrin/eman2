#!/usr/bin/env bash

SRC_DIR="$(cd ../.. "$(dirname "$0")"; pwd -P)"
progs=$( find "${SRC_DIR}/programs" -name 'e2*.py' -exec basename {} \; )

for f in ${progs[@]};do
    prog=${f%%.py}
    echo "Extracting from ${SRC_DIR}/programs/$f into $prog.txt"
    python "${SRC_DIR}"/examples/extracthelp.py "${SRC_DIR}"/programs/$f > ${prog}.txt
done
