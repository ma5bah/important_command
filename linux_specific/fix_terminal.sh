#!/usr/bin/env zsh
# -------------------------------------------------------------------
# Linux ZSH Key Bindings
# Source this file from ~/.zshrc:  source /path/to/fix_terminal.sh
# -------------------------------------------------------------------

# Guard against double-sourcing
[[ -n "$_FIX_TERMINAL_LOADED" ]] && return
_FIX_TERMINAL_LOADED=1

# Ensure we are using emacs mode (standard for word jumping)
bindkey -e

# Use bash-like word boundaries (stop at /, ., - etc.)
WORDCHARS='*?[]~=&;!#$%^(){}<>'

# --- Word Jumping (Alt + Arrows) ---
# ESC + CSI arrow — some terminals send this for Alt+Arrow
bindkey "^[^[[D" backward-word
bindkey "^[^[[C" forward-word
# Alt+Left/Right — xterm modifier format (xterm/GNOME/Konsole)
bindkey "^[[1;3D" backward-word
bindkey "^[[1;3C" forward-word
# Ctrl+Left/Right — xterm, GNOME Terminal, Konsole
bindkey "^[[1;5D" backward-word
bindkey "^[[1;5C" forward-word
# rxvt legacy
bindkey "^[[5D" backward-word
bindkey "^[[5C" forward-word
# Standard emacs Alt+B / Alt+F (already active via -e, explicit for clarity)
bindkey "^[b" backward-word
bindkey "^[f" forward-word

# --- Word Deletion ---
# Alt+Backspace — delete word backward
bindkey "^[^?" backward-kill-word
# Ctrl+W — standard unix word-kill
bindkey "^W" backward-kill-word
# Ctrl+Delete — delete word forward
bindkey "^[[3;5~" kill-word
# Alt+D — standard emacs forward word-kill
bindkey "^[d" kill-word

# --- Line Navigation (Home/End) ---
# CSI sequences (normal mode)
bindkey "^[[H" beginning-of-line
bindkey "^[[F" end-of-line
# VT220 / older terminals
bindkey "^[[1~" beginning-of-line
bindkey "^[[4~" end-of-line
# Application mode (GNOME Terminal, Konsole)
bindkey "^[OH" beginning-of-line
bindkey "^[OF" end-of-line

# --- Intelligent History Search ---
# Type a few letters and press Up/Down to cycle through matching history
if autoload -Uz up-line-or-beginning-search down-line-or-beginning-search 2>/dev/null; then
    zle -N up-line-or-beginning-search
    zle -N down-line-or-beginning-search
    bindkey "^[[A" up-line-or-beginning-search
    bindkey "^[[B" down-line-or-beginning-search
fi

# --- Handy Shortcuts ---
bindkey '^U' backward-kill-line
bindkey '^K' kill-line
# Reverse menu completion (Shift+Tab)
bindkey '^[[Z' reverse-menu-complete