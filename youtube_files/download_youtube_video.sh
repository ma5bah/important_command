#!/bin/bash

# OS Detection (remains the same)
if echo "$(uname -a)" | grep "Android"; then
        detected_os="android"
elif echo "$(uname -a)" | grep "Darwin"; then
        detected_os="macos"
elif echo "$(uname -a)" | grep "Linux"; then
        detected_os="linux"
else
        detected_os="windows"
        echo " I am Windows, Some functionalities may not work"
fi

# Ensure python3 and pip3 are installed (prerequisite for 'pip3 install uv')
if [[ ! $(which python3) || ! $(which pip3) ]]; then
        echo "python3 or pip3 not found, attempting to install..."
        if [[ $detected_os == "android" ]]; then
                pkg install python3
        elif [[ $detected_os == "linux" ]]; then
                sudo apt-get update && sudo apt-get install -y python3 python3-pip
        elif [[ $detected_os == "macos" ]]; then
                brew install python3 # Homebrew typically installs pip with python
        else
                echo "python3 or pip3 not found. Please install them to proceed."
                exit 1
        fi
fi

# Check if uv is installed, if not install it using pip3
if ! command -v uv &> /dev/null; then
        if [[ $detected_os == "android" ]]; then
                pkg install uv;
                continue;
        fi


        echo "uv not found. Attempting to install with pip3..."
        echo "Note: The official uv documentation (https://docs.astral.sh/uv/getting-started/installation/)"
        echo "primarily recommends standalone installers (e.g., via curl or PowerShell) or pipx."
        echo "Using 'pip3 install uv' as per your request."
        pip3 install uv

        # Ensure uv is in PATH. For user installs via pip, it might be in ~/.local/bin.
        # This step is crucial if pip installs scripts to a directory not in the default PATH.
        if ! command -v uv &> /dev/null; then
            echo "'uv' command still not found after pip3 install."
            echo "Please ensure the directory where pip installs executables is in your PATH."
            echo "Common locations include: ~/.local/bin (for Linux/macOS user installs)."
            # Attempt to add common user bin directory to PATH for the current session
            if [[ -d "$HOME/.local/bin" ]] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
                export PATH="$HOME/.local/bin:$PATH"
                echo "Temporarily added $HOME/.local/bin to PATH. If 'uv' now works, add this to your shell profile (e.g., .bashrc, .zshrc)."
                if ! command -v uv &> /dev/null; then
                   echo "'uv' still not found. Please resolve PATH issues manually."
                   exit 1
                fi
            else
                exit 1
            fi
        fi
fi
echo "uv is available."

# Create virtualenv using uv (uv creates .venv by default if not in a project)
# According to docs, 'uv venv' is the command.
if [[ ! -d .venv ]]; then
        echo "Creating virtual environment '.venv' using uv..."
        uv venv .venv # Explicitly naming it, though often not needed
fi

# Activate virtualenv
echo "Activating virtual environment..."
if [[ $detected_os == "windows" ]]; then
        source .venv/Scripts/activate;
else
        source .venv/bin/activate;
fi

# Install yt-dlp using uv's pip interface
echo "Installing/Updating yt-dlp using 'uv pip install'..."
uv pip install yt-dlp;

# Check ffmpeg and aria2c (remains the same)
if [[ ! $(which ffmpeg) || ! $(which aria2c) ]]; then
        echo "ffmpeg or aria2c not found, attempting to install..."
        if [[ $detected_os == "android" ]]; then
                pkg install ffmpeg aria2
        elif [[ $detected_os == "linux" ]]; then
                sudo apt-get install -y ffmpeg aria2
        elif [[ $detected_os == "macos" ]]; then
                brew install ffmpeg aria2
        else
                echo "ffmpeg or aria2c not found. On Windows, please install them manually and ensure they are in your PATH."
                # Decide if this should be a fatal error for Windows
        fi
fi

# Parsing arguments (remains the same)
while [[ "$#" -gt 0 ]]; do
        case $1 in
        -p | --path | --download_path)
                download_path="$2"
                shift
                ;;
        -u | --url | --youtube_url)
                youtube_url="$2"
                shift
                ;;
        -of | --output_format)
                output_format="$2"
                shift
                ;;
        -id | --is_id_needed)
                is_id_needed="$2"
                shift
                ;;
        -mw | --max_workers)
                max_workers="$2"
                shift
                ;;
        -h | --help)
                echo "Example usage :"
                echo "  -p | --path | --download_path : /path/to/download"
                echo "  -u | --url | --youtube_url : <youtube_url_or_id>"
                echo "  -of | --output_format : avi | flv | mkv | mov | mp4 | webm (default mkv)"
                echo "  -id | --is_id_needed : 0 | 1 (default 1) Add ID to the file name"
                echo "  -mw | --max_workers : 1 | 2 | 3 | 4 | 5 (default 5) Number of threads to use"
                exit 0 # Changed to exit 0 for help
                ;;
        *)
                if [[ $1 == *"youtube.com"* || $1 == *"youtu.be"* || $1 == *"youtube.com"* || $1 == *"youtu.be"* ]]; then # Made URL check more general
                        youtube_url=$1
                        # Do not break here if other parameters might follow the URL
                else
                        echo "Unknown parameter passed or invalid URL (if positional): $1"
                        echo "Use -h or --help for usage."
                        exit 1
                fi
                ;;
        esac
        shift
done

# Default and Validation logic (remains largely the same, minor adjustments)
if [[ -z "$youtube_url" ]]; then # Check if youtube_url is empty
        echo "No youtube url provided. Use -u <url>."
        exit 1
fi

if [[ ! -d "$download_path" ]]; then # Check if download_path is not a directory or not set
        echo "Download path '$download_path' not found or not specified. Setting default."
        if [[ $detected_os == "android" ]]; then
                download_path="/storage/emulated/0/Download/youtube/"
        elif [[ $detected_os == "linux" ]]; then
                # Using user's Downloads directory as a more generic default
                download_path="$HOME/Downloads/youtube/"
                # The sda2 mount logic is very specific; a general default is better for a generic script
                # if [[ ! $(findmnt -M "/media/ma5bah/sda2") ]]; then
                #         echo "Mounting sda2, Enter Password : "
                #         sudo mount /dev/sda2 /media/ma5bah/sda2 || { echo "Failed to mount sda2"; exit 1; }
                # fi
        elif [[ $detected_os == "macos" ]]; then
                download_path="$HOME/Downloads/youtube/"
        else # windows or other
                download_path="./youtube_downloads/" # Default to a local subdirectory
        fi
        echo "Defaulting download path to: $download_path"
fi

# Create download directory if it doesn't exist
if [[ ! -d "$download_path" ]]; then
    echo "Creating download directory: $download_path"
    mkdir -p "$download_path" || { echo "Failed to create download directory: $download_path"; exit 1; }
fi


is_id_needed=${is_id_needed:-1} # Simpler default assignment
max_workers=${max_workers:-5}

valid_formats=("avi" "flv" "mkv" "mov" "mp4" "webm")
is_valid_format=0
for fmt in "${valid_formats[@]}"; do
    if [[ "$output_format" == "$fmt" ]]; then
        is_valid_format=1
        break
    fi
done

if [[ $is_valid_format -eq 0 ]]; then
    if [[ -n "$output_format" ]]; then # If output_format was set but invalid
        echo "Invalid output format '$output_format'. Defaulting to mkv."
    fi
    output_format="mkv" # Default output format
fi

# Check each variable value
echo "--- Configuration ---"
echo "Download Path : $download_path"
echo "YouTube URL   : $youtube_url"
echo "Output Format : $output_format"
echo "Add ID        : $is_id_needed"
echo "Max Workers   : $max_workers"
echo "---------------------"

echo "Starting download process..."
# Execute the python script
# Ensure the python3 in the venv is used if 'python3' might point elsewhere
# Using 'python' is often safer within an activated venv as it refers to venv's python
python download_youtube.py \
        --download_path "$download_path" \
        --output_format "$output_format" \
        --is_id_needed "$is_id_needed" \
        --max_workers "$max_workers" \
        --youtube_url "$youtube_url";

echo "Script finished."
deactivate # Deactivate the virtual environment