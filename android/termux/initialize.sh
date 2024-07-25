pkg update && pkg upgrade;

pkg install git python clang;

# install yt-dlp and ffmpeg
pip install yt-dlp ffmpeg;

# initialize keyboard
echo "enforce-char-based-input = true" >> ~/.termux/termux.properties;

termux-setup-storage

# install go
pkg install golang;

# install tools
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

