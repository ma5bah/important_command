#cat /sys/class/power_supply/BAT1/capacity;
echo "Laptop Charge : $(cat /sys/class/power_supply/BAT1/capacity)"%;



for i in {100..255}; do nmap -p5900 -Pn 192.168.0.$i && echo 192.168.0.$i; done
