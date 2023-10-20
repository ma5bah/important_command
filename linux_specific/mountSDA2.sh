if [[ $(findmnt -M "/media/ma5bah/sda2") ]]; then
	echo "Already mounted";
else
    	sudo mount /dev/sda2 /media/ma5bah/sda2;
fi
