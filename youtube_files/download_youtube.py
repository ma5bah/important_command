import shutil
import sys
from time import sleep
import yt_dlp
import threading
import os
import argparse
import concurrent.futures


# Function to extract playlist information using yt-dlp
def extract_playlist_info(playlist_url, output_format, is_id_needed):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "dump_single_json": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)

    video_entries = []
    if "list" in playlist_url:
        playlist_id = playlist_info["id"]
        playlist_title = playlist_info["title"]
        playlist_count = str(playlist_info.get("playlist_count"))
        for idx, entry in enumerate(playlist_info.get("entries", [])):
            final_output_path = f"playlists/{playlist_title}[_id_]{playlist_id}/{str(idx+1).zfill(len(playlist_count))}-{entry.get('title')}-{entry.get('id')}.{output_format}"
            if not is_id_needed:
                final_output_path = f"playlists/{playlist_title}[_id_]{playlist_id}/{entry.get('title')}-{entry.get('id')}.{output_format}"
            video_details = {
                "id": entry.get("id"),
                "title": entry.get("title"),
                "url": entry.get("url"),
                "output_path": final_output_path
            }
            video_entries.append(video_details)
    else:
        video_details = {
            "id": playlist_info.get("id"),
            "title": playlist_info.get("title"),
            "url": f"https://www.youtube.com/watch?v={playlist_info.get('id')}",
            "output_path": f"individual_downloads/{playlist_info.get('title')}[_id_]{playlist_info.get('id')}.{output_format}",
        }
        video_entries.append(video_details)

    return video_entries


# Lock for thread-safe file writing
lock = threading.Lock()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos and playlists."
    )
    parser.add_argument("--download_path", help="Path to download", default=os.getcwd())
    parser.add_argument("--youtube_url", help="YouTube URL", required=True)
    parser.add_argument(
        "--output_format",
        help="Output format (avi, flv, mkv, mov, mp4, webm)",
        default="mkv",
    )
    parser.add_argument("--max_workers", help="Number of threads to use", default=5)
    parser.add_argument("--is_id_needed", help="Add ID to the file name", default=1)
    return parser.parse_args()


def fetch_data(video_entry, output_format, download_path):
    print(f"Downloading: {video_entry['title']} ({video_entry['url']})")
    output_file_path = os.path.join(download_path, video_entry["output_path"])
    output_dir = os.path.dirname(output_file_path)

    with lock:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    ydl_opts = {
        "format": "bestvideo*+bestaudio/best",
        "outtmpl": output_file_path,
        "embed_thumbnail": True,
        "embed_metadata": True,
        "embed_chapters": True,
        "merge_output_format": output_format,
        "ffmpeg_location": shutil.which("ffmpeg"),
        "external_downloader": shutil.which("aria2c"),
        "external_downloader_args": [
            "--max-concurrent-downloads=16",
            "--max-connection-per-server=8",
            "--split=5",
        ],
        "audio_quality": 0,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_entry["url"]])


def main():
    args = parse_args()
    youtube_url = args.youtube_url
    download_path = args.download_path
    output_format = args.output_format
    if not str(args.max_workers).isdecimal():
        print("Max Workers should be a number")
        sys.exit(1)
    max_workers = int(args.max_workers)
    if not str(args.is_id_needed).isdecimal():
        print("ID should be a number")
        sys.exit(1)
    is_id_needed = bool(int(args.is_id_needed))
    print(f"Downloading to: {download_path}")
    print(f"Output format: {output_format}")
    print(f"Max workers: {max_workers}")
    print(f"Is ID needed: {is_id_needed}")


    video_entries = extract_playlist_info(youtube_url, output_format,is_id_needed)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_data, entry, output_format, download_path)
            for entry in video_entries
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
