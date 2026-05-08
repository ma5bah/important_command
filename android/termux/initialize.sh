pkg update && pkg upgrade -y;

# Termux host packages: keep these limited to Android/Termux integration.
pkg install -y proot-distro termux-api which git python clang;

# initialize keyboard
echo "enforce-char-based-input = true" >> ~/.termux/termux.properties;

termux-setup-storage

# install proot-distro and debian
proot-distro install debian;
proot-distro login debian -- bash -lc '
  apt update &&
  apt upgrade -y &&
  apt install -y git python3 python3-pip python3-venv clang golang ffmpeg &&
  python3 -m pip install --user yt-dlp &&
  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
';
