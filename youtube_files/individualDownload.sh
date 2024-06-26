#!/bin/bash

# Extracting arguments from command line
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--path|--download_path) download_path="$2"; shift ;;
        -u|--url|--youtube_url) youtube_url="$2"; shift ;;
        -of|--output_format) output_format="$2"; shift ;;
        -h|--help) echo "Example usage :";
                echo "  -p | --path | --download_path : /path/to/download";
                echo "  -u | --url | --youtube_url : https://www.youtube.com/watch?v=xxxxxxxxxxx | https://www.youtube.com/playlist?list=xxxxxxxxxxx"; 
                exit 1 ;;
        *) 
                if [[ $1 == *"youtube.com"* || $1 == *"youtu.be"* ]]; then
                        youtube_url=$1;
                        break;
                fi
                echo "Unknown parameter passed: $1";
                echo "Example usage :";
                echo "  -p | --path | --download_path : /path/to/download";
                echo "  -u | --url | --youtube_url : https://www.youtube.com/watch?v=xxxxxxxxxxx | https://www.youtube.com/playlist?list=xxxxxxxxxxx"; 
                echo "  -of | --output_format : avi | flv | mkv | mov | mp4 | webm";
                exit 1 ;;
    esac
    shift
done

if [[ $youtube_url != *"youtube.com"* && $youtube_url != *"youtu.be"* ]]; then
        echo "No youtube url provided";
        exit 1;
fi
if [[ ! -d $download_path ]]; then
        if [[ ! $(uname) == "Darwin" ]]; then
                # if not macos
                download_path="/media/ma5bah/sda2/DownLoad/youtube/"
                if [[ ! $(findmnt -M "/media/ma5bah/sda2") ]]; then
                        echo "Mounting sda2, Enter Password : ";
                        sudo mount /dev/sda2 /media/ma5bah/sda2;
                fi
        else
                download_path="."
        fi
fi
if [[ ! -d $output_format && $output_format != "avi" && $output_format != "flv" && $output_format != "mkv" && $output_format != "mov" && $output_format != "mp4" && $output_format != "webm" ]]; then
        # default output format is mkv
        output_format="mkv";
fi

if [[ $youtube_url == *"list"* ]]; then
        # if youtube_url is a playlist
        $output_path='playlists/%(playlist_title)s[_id_]%(playlist_id)s/%(playlist_index)s-%(title)s-%(id)s.%(ext)s';
else
        # if youtube_url is a video
        $output_path='individual_downloads/%(title)s-%(id)s.%(ext)s';
fi

cd $download_path;
yt-dlp \
  --format bestvideo*+bestaudio/best \
  --output  $output_path \
  --embed-thumbnail --embed-metadata --embed-chapters \
  --merge-output-format $output_format \
  --concurrent-fragments 5 \
  --audio-quality 0 $youtube_url;
#  --downloader '/usr/bin/aria2c' $1;