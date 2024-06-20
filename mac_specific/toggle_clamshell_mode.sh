#!/bin/bash

if [ "$(pmset -g | grep hibernatemode | awk '{print $2}')" == 3 ]; then
    sudo pmset -a sleep 0;
    sudo pmset -a hibernatemode 0;
    sudo pmset -a disablesleep 1;
    echo "I am in Clamshell mode without power adapter"
    echo "I can't sleep or hibernate"
else
    sudo pmset -a sleep 1
    sudo pmset -a hibernatemode 3
    sudo pmset -a disablesleep 0
    echo "I have exited Clamshell mode without power adapter"
    echo "I can sleep and hibernate"
fi
