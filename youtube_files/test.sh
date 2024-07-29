#!/bin/bash

# check if ffmpeg and aria2c are installed
if [[ ! $(command -v ffmpeg) ]]; then
        echo "ffmpeg not installed";
        exit 1;
fi

echo "ffmpeg_path : $(command -v ffmpeg)";