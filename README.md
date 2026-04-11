# dotfiles

Run `source dotfiles/runpod.sh` to set up.

## Notes

Use the following commands for most workflows.

```bash
    "remote.SSH.defaultExtensions": [
        "ms-python.python",
        "ms-toolsai.jupyter",
        "charliermarsh.ruff",
        "tamasfe.even-better-toml",
        "wholroyd.jinja",
    ],
```

Also add this to your user settings if you want to use `.bashrc` variables in Jupyter notebooks.

```bash
    "jupyter.runStartupCommands": [
        "import dotenv",
        "dotenv.load_dotenv('/root/.bashrc')"
    ],
```

This repository uses Runpod Environment Variables to login.


## Commands

Copy my zsh theme from dotfiles to the zsh config directory.
`cp ~/Programming/dotfiles/cadentj.zsh-theme $ZSH_CUSTOM/themes/cadentj.zsh-theme`


# My Mac Settings

Apps: 
- [Rectangle](https://rectangleapp.com/) - 
- [Obsidian](https://obsidian.md/) -
- [Ghostty](https://ghostty.org/)
  - [Quick Terminal](https://ghostty.org/docs/config/keybind/reference#toggle_quick_terminal) is great. I use it over spotlight search.