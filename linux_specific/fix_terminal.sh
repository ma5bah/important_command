#!/bin/sh

[ -n "$_FIX_TERMINAL_LOADED" ] && return 0 2>/dev/null
_FIX_TERMINAL_LOADED=1

command -v infocmp >/dev/null 2>&1 && ! infocmp "$TERM" >/dev/null 2>&1 && export TERM=xterm-256color
stty erase '^?' 2>/dev/null

# Zsh-only init (must run before unified bindings)
if [ -n "$ZSH_VERSION" ]; then
  bindkey -e
  WORDCHARS='*?[]~=&;!#$%^(){}<>'
  KEYTIMEOUT=10
  autoload -Uz up-line-or-beginning-search down-line-or-beginning-search 2>/dev/null
  zle -N up-line-or-beginning-search 2>/dev/null
  zle -N down-line-or-beginning-search 2>/dev/null
  _ft_smkx() { echoti smkx 2>/dev/null; }
  _ft_rmkx() { echoti rmkx 2>/dev/null; }
  if autoload -Uz add-zle-hook-widget 2>/dev/null; then
    add-zle-hook-widget line-init _ft_smkx; add-zle-hook-widget line-finish _ft_rmkx
  else
    zle -N zle-line-init _ft_smkx; zle -N zle-line-finish _ft_rmkx
  fi
  autoload -Uz bracketed-paste-magic 2>/dev/null && zle -N bracketed-paste bracketed-paste-magic
fi

# Unified bind: _bind <seq> <action> [bash_override]
# Translates zsh ^[ notation to bash \e notation automatically.
_bind() {
  _s="$1" _za="$2" _ba="${3:-$2}"
  if [ -n "$ZSH_VERSION" ]; then
    bindkey "$_s" "$_za" 2>/dev/null
  elif [ -n "$BASH_VERSION" ]; then
    _bs=$(printf '%s' "$_s" | sed 's/\^\[/\\e/g;s/\^\?/\\C-?/g;s/\^W/\\C-w/;s/\^U/\\C-u/;s/\^K/\\C-k/;s/\^L/\\C-l/')
    bind "\"$_bs\": $_ba" 2>/dev/null
  fi
}

# Word jumping
_bind "^[^[[D" backward-word;    _bind "^[^[[C" forward-word      # double-ESC arrow
_bind "^[[1;3D" backward-word;   _bind "^[[1;3C" forward-word
_bind "^[[1;5D" backward-word;   _bind "^[[1;5C" forward-word
_bind "^[[5D" backward-word;     _bind "^[[5C" forward-word        # rxvt
_bind "^[Od" backward-word;      _bind "^[Oc" forward-word         # rxvt ctrl+arrow
_bind "^[b" backward-word;       _bind "^[f" forward-word

# Word deletion
_bind "^[^?" backward-kill-word
_bind "^W" backward-kill-word
_bind "^[[3;5~" kill-word;       _bind "^[[3;3~" kill-word
_bind "^[d" kill-word

# Home / End
_bind "^[[H" beginning-of-line;  _bind "^[[F" end-of-line
_bind "^[OH" beginning-of-line;  _bind "^[OF" end-of-line          # SS3 / app mode
_bind "^[[1~" beginning-of-line; _bind "^[[4~" end-of-line         # VT220
_bind "^[[7~" beginning-of-line; _bind "^[[8~" end-of-line         # rxvt

# Delete key
_bind "^[[3~" delete-char

# History search (zsh: prefix-aware, bash: basic search)
_bind "^[[A" up-line-or-beginning-search history-search-backward
_bind "^[[B" down-line-or-beginning-search history-search-forward
_bind "^[OA" up-line-or-beginning-search history-search-backward   # app mode
_bind "^[OB" down-line-or-beginning-search history-search-forward

# Shortcuts
_bind "^U" backward-kill-line
_bind "^K" kill-line
_bind "^L" clear-screen
_bind "^[[Z" reverse-menu-complete                                 # shift+tab

unset -f _bind 2>/dev/null

# Handles: app/normal mode, tmux/screen, SSH TERM mismatch, ^H/^? backspace,
# smkx/rmkx hooks, WORDCHARS, KEYTIMEOUT, delete key, paste bracket mode,
# double-ESC seqs, rxvt legacy. macOS needs "Use Option as Meta" in terminal.




# Edge cases handled:
#  1. App vs Normal mode — CSI + SS3 bound     
#  2. tmux/screen — rxvt/VT220 variants        
#  3. SSH TERM mismatch — auto-fallback         
#  4. Backspace ^H/^? — stty erase fix         
#  5. macOS Option — needs "Meta" in term app   
#  6. Vi mode / framework overrides            
#  7. WORDCHARS clobbering (zsh)
#  8. ZLE smkx/rmkx hooks (zsh)
#  9. Delete key variants
# 10. Double-escape arrow seqs
# 11. Escape delay (KEYTIMEOUT)
# 12. Paste bracket mode (zsh)