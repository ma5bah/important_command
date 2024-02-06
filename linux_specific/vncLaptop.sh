#!/usr/bin/bash

/usr/bin/x11vnc -auth guess -forever -loop -noxdamage -repeat -rfbauth /home/ma5bah/.vnc/passwd -rfbport 5900 -shared;
