#!/bin/bash
source octoprint.rc || customDie "octoprint.rc must be in the same directory from which you run $0."
if [ "$USER" != "$UNPRIV_USER" ]; then
    customDie "You must be pi to run this script. See octoprint.sh."
fi
#SUDOER="$USER"
# See https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspbian/2337
cd ~
#sudo apt update
#sudo apt install python-pip python-dev python-setuptools python-virtualenv git libyaml-dev build-essential
mkdir OctoPrint && cd OctoPrint
virtualenv venv
source venv/bin/activate
pip install pip --upgrade
pip install octoprint
deactivate

#cd ~
#sudo usermod -a -G tty $UNPRIV_USER
#sudo usermod -a -G dialout $UNPRIV_USER

#wget https://github.com/foosel/OctoPrint/raw/master/scripts/octoprint.init && sudo mv octoprint.init /etc/init.d/octoprint
#wget https://github.com/foosel/OctoPrint/raw/master/scripts/octoprint.default && sudo mv octoprint.default /etc/default/octoprint
#sudo chmod +x /etc/init.d/octoprint
#sudo echo "DAEMON=`pwd`/venv/bin/octoprint" >> /etc/default/octoprint
#sudo echo "OCTOPRINT_USER=$UNPRIV_USER" >> /etc/default/octoprint

