# Caden's dotfiles

## Mac

Apps: 
- [Rectangle](https://rectangleapp.com/) - Fast window tiling. Slimmer than Yabai + skhd.
  - Loads from `RectangleConfig.json`
- [Obsidian](https://obsidian.md/) -
  - I have a couple hotkeys at `hotkeys.json` which map to keybinds similar to the ones I use in Cursor. E.g.
    - `cmd + P` for the file picker
    - `cmd + shift P` for a command palette
    - `cmd + \` for splitting the current window
- [Ghostty](https://ghostty.org/)
  - [Quick Terminal](https://ghostty.org/docs/config/keybind/reference#toggle_quick_terminal) is great. I unmap spotlight search from `cmd + space` and use a small launcher program instead. Spotlight search tends to bring up a bunch of unrelated results + is slow.
  - Load the config at `config.ghostty`.


Sort of an unsorted note atm, but I was pretty confused why my terminal was taking a second to startup, apparently NVM was always loading so I added some scripts Codex gave me for lazy loading in `lazy_nvm.sh`.

## Tools

`docs`

## Runpod

I use Runpod as a GPU workspace for work sometimes.

Run `source dotfiles/runpod.sh` to set up.

## Cursor / VSCode

Use the following commands for most workflows.

```bash
    "remote.SSH.defaultExtensions": [
        "ms-python.python",
        "ms-toolsai.jupyter",
        "charliermarsh.ruff",
        "tamasfe.even-better-toml",
        "wholroyd.jinja",
        "ziruiwang.nvidia-monitor",
        "ms-python.debugpy"
    ],
```

Also add this to your user settings if you want to use `.bashrc` variables in Jupyter notebooks.

```bash
    "jupyter.runStartupCommands": [
        "import dotenv",
        "dotenv.load_dotenv('/root/.bashrc')"
    ],
```