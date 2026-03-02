reload config 
`tmux source-file ~/.tmux.conf`

install tmux files
`git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm`

install plugins
`prefix + I`

config
```bash
set -g @plugin 'azorng/tmux-smooth-scroll'
set -g status-style "bg=blue"

# Enable on mouse wheel scroll
# set -g @smooth-scroll-mouse "true"

# This line must be at the very bottom of tmux.conf
run '~/.tmux/plugins/tpm/tpm'
```