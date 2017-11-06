
files=$(find ../eman2-qt5 -type file)

for f in ${files[@]};do
	dest=${f##../eman2-qt5/}
	mv -v $f $dest
done
