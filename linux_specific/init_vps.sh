#!/bin/bash

# Intalling golang
# Instructions:
echo "Installing Golang"
wget https://dl.google.com/go/go1.22.5.linux-amd64.tar.gz
sudo tar -xvf go1.22.5.linux-amd64.tar.gz
sudo mv go /usr/local
export GOROOT=/usr/local/go
export GOPATH=$HOME/go
export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
echo 'export GOROOT=/usr/local/go' >>~/.bash_profile
echo 'export GOPATH=$HOME/go' >>~/.bash_profile
echo 'export PATH=$GOPATH/bin:$GOROOT/bin:$PATH' >>~/.bash_profile
source ~/.bash_profile

# Installing Python3 and pip3
# Instructions:
sudo apt-get install -y python3 python3-pip

# Installing Node JS with Necessary Packages
# Instrucitons:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

# Installing pnpm package manager
# Instructions:
sudo npm install -g pnpm
pnpm setup

# Installing Web essentials, such as nginx, pm2, certbot, postgresql-client
# Instructions:
sudo apt-get install -y nginx certbot python3-certbot-nginx postgresql-client
sudo pnpm install -g pm2

# Installing openvpn server with configuration
# https://github.com/angristan/openvpn-install/raw/master/openvpn-install.sh
