#!/usr/bin/env python3

# WARNING: do NOT do a relative import, this file must be directly executable
# by filename
from codemcp import cli, mcp

__all__ = ["mcp"]

if __name__ == "__main__":
    # Use Click's CLI interface instead of directly calling run()
    cli()
