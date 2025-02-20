# dotfiles

Adopted from [John Hughes](https://github.com/jplhughes/dotfiles/tree/master).

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
