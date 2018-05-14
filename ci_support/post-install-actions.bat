call %PREFIX%\Scripts\activate.bat

conda.exe info -a
conda.exe list

conda.exe install eman-deps=9.1 -c cryoem -c defaults -c conda-forge -y
