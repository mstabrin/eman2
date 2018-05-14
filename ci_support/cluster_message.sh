#!/usr/bin/env bash

source ${PREFIX}/bin/activate

conda info -a
conda list

if [ "$(uname -s)" == "Linux" ];then
    conda install eman-deps=9 -c cryoem -c defaults -c conda-forge -y
fi

cat <<EOF

INSTALLATION IS NOW COMPLETE

Please, go to http://blake.bcm.edu/emanwiki/EMAN2/Install/BinaryInstallAnaconda
for detailed installation instructions, testing and troubleshooting information.
If this installation is on a Linux cluster,
you will require additional steps before installation is complete!

EOF
