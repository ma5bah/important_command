#!/bin/bash
if [[ ! $(findmnt -M "/media/ma5bah/sda2") ]]; then
	echo "Mounting sda2, Enter Password : ";
	sudo mount /dev/sda2 /media/ma5bah/sda2;
fi
URL="$1";
if [[ $URL == *"list"* ]]; then
    yt-dlp \
        --format bestvideo*+bestaudio/best \
        --output 'playlists/%(playlist_title)s[_id_]%(playlist_id)s/%(playlist_index)s-%(title)s-%(id)s.%(ext)s' \
        --embed-thumbnail --embed-metadata --embed-chapters \
        --concurrent-fragments 5 \
        --audio-quality 0 \
        --ffmpeg-location '/usr/bin/ffmpeg' \
        --downloader '/usr/bin/aria2c' $1;
else
    yt-dlp \
        --format bestvideo*+bestaudio/best \
        --output 'individual_downloads/%(title)s-%(id)s.%(ext)s' \
        --embed-thumbnail --embed-metadata --embed-chapters \
        --concurrent-fragments 5 \
        --audio-quality 0 \
        --ffmpeg-location '/usr/bin/ffmpeg' \
        --downloader '/usr/bin/aria2c' $1;
fi
# list= echo $URL | grep -E "list" ;
