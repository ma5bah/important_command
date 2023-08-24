#!/bin/bash

sudo pmset -a sleep 0;
sudo pmset -a hibernatemode 0;
sudo pmset -a disablesleep 1;


# You can always revert the changes by running the following commands

# sudo pmset -a sleep 1
# sudo pmset -a hibernatemode 3
# sudo pmset -a disablesleep 0
