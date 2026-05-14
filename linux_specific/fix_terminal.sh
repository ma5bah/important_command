#!/usr/bin/env bash


# Fix for the "Double Escape" sequence identified via cat -v
bindkey "^[^[[D" backward-word
bindkey "^[^[[C" forward-word

# Also include the single-escape versions just in case 
# (Standard for most Linux/Mac terminal defaults)
bindkey "^[b" backward-word
bindkey "^[f" forward-word
bindkey "^[[1;3D" backward-word
bindkey "^[[1;3C" forward-word