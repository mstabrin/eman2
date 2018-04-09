#!/usr/bin/env bash

SRC_DIR="$(cd ../.. "$(dirname "$0")"; pwd -P)"
progs=$( find "${SRC_DIR}/programs" -name 'e2*.py' -exec basename {} \; )

progs_exclude=( e2.py e2projectmanager.py e2unwrap3d.py e2version.py e2fhstat.py e2_real.py 
                e2proc3d.py         # uses OptionParser
)

for f in ${progs_exclude[@]};do
    progs=( ${progs[@]/$f} )
done

for f in ${progs[@]};do
    prog=${f%%.py}
    echo "Extracting from ${SRC_DIR}/programs/$f into $prog.txt"
    $f --generate_doc > ${prog}.txt
done
