set -e  # Stop the script on any error
echo "127.0.0.1 mininet-wifi" >> /etc/hosts             #To enable the usage of sudo
echo "Starting setup"



echo 'deb http://archive.debian.org/debian stretch main contrib non-free' > /etc/apt/sources.list; 
echo 'deb http://archive.debian.org/debian-security stretch/updates main contrib non-free' >> /etc/apt/sources.list; 
echo 'Acquire::Check-Valid-Until \"false\";' | tee /etc/apt/apt.conf.d/99no-check-valid-until; 
chmod 777 /tmp;                 #SO PARA AS ISNTALAÇOES APT
apt update
apt install -y liberror-perl git ncurses-bin wget sudo iputils-ping x11-apps x11-utils xterm; 


wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
python get-pip.py
pip install scapy datetime


#git clone https://github.com/intrig-unicamp/mininet-wifi || echo "Already cloned mininet-wifi"
#cd mininet-wifi
#sudo util/install.sh -Wln

#sudo mn --wifi
#sudo mn --wifi --mac --arp --ap p4ap --client-isolation

#cd ..


python mininet/topo.py