from mcp.server.fastmcp import FastMCP
import subprocess

mcp = FastMCP("git")

def run_git(*args, cwd="/home/sprite/sinnoh"):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return result.stdout + result.stderr

@mcp.tool()
def git_status() -> str:
    """Show working tree status"""
    return run_git("status")

@mcp.tool()
def git_diff(staged: bool = False) -> str:
    """Show changes. Set staged=True for staged changes."""
    return run_git("diff", "--cached") if staged else run_git("diff")

@mcp.tool()
def git_log(count: int = 10) -> str:
    """Show recent commits"""
    return run_git("log", "--oneline", f"-{count}")

@mcp.tool()
def git_add(files: str = ".") -> str:
    """Stage files. Use '.' for all, or space-separated paths."""
    return run_git("add", *files.split())

@mcp.tool()
def git_commit(message: str) -> str:
    """Create a commit with the given message"""
    return run_git("commit", "-m", message)

@mcp.tool()
def git_checkout(branch: str, create: bool = False) -> str:
    """Switch branches. Set create=True to create a new branch."""
    if create:
        return run_git("checkout", "-b", branch)
    return run_git("checkout", branch)

@mcp.tool()
def git_branches() -> str:
    """List all branches"""
    return run_git("branch", "-a")

@mcp.tool()
def git_push(remote: str = "origin", branch: str = "") -> str:
    """Push commits to remote"""
    args = ["push", remote]
    if branch:
        args.append(branch)
    return run_git(*args)

@mcp.tool()
def git_pull(remote: str = "origin", branch: str = "") -> str:
    """Pull from remote"""
    args = ["pull", remote]
    if branch:
        args.append(branch)
    return run_git(*args)

@mcp.tool()
def gh_pr_create(title: str, body: str = "", base: str = "main") -> str:
    """Create a GitHub PR for the current branch"""
    cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    result = subprocess.run(cmd, cwd="/home/sprite/sinnoh", capture_output=True, text=True)
    return result.stdout + result.stderr

mcp.run(transport="stdio")