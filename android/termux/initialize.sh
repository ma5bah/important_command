pkg update && pkg upgrade;

pkg install git python clang;

# initialize keyboard
echo "enforce-char-based-input = true" >> ~/.termux/termux.properties;

termux-setup-storage