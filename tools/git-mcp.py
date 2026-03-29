from mcp.server.fastmcp import FastMCP # type: ignore
import subprocess

mcp = FastMCP("git-mcp")

DEFAULT_CWD = "/home/sprite/sinnoh"


def run_git(*args, cwd=DEFAULT_CWD):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return result.stdout + result.stderr


@mcp.tool()
def git_status() -> str:
    """Show working tree status."""
    return run_git("status")


@mcp.tool()
def git_diff(staged: bool = False) -> str:
    """Show changes; use staged=True for staged diff only.

    Args:
        staged: When True, show staged changes (--cached).
    """
    return run_git("diff", "--cached") if staged else run_git("diff")


@mcp.tool()
def git_log(count: int = 10) -> str:
    """Show recent commits (oneline).

    Args:
        count: Number of commits to show.
    """
    return run_git("log", "--oneline", f"-{count}")


@mcp.tool()
def git_add(files: str = ".") -> str:
    """Stage files for commit.

    Args:
        files: Paths to stage, space-separated, or '.' for all.
    """
    return run_git("add", *files.split())


@mcp.tool()
def git_commit(message: str) -> str:
    """Create a commit with the given message.

    Args:
        message: Commit message.
    """
    return run_git("commit", "-m", message)


@mcp.tool()
def git_sync(
    message: str,
    remote: str = "origin",
    branch: str = "",
) -> str:
    """Stage all changes (git add .), commit, and push in one step.

    Args:
        message: Commit message.
        remote: Remote name to push to.
        branch: Branch to push; leave empty to use the default upstream behavior.
    """
    parts = [
        run_git("add", "."),
        run_git("commit", "-m", message),
    ]
    push_args = ["push", remote]
    if branch:
        push_args.append(branch)
    parts.append(run_git(*push_args))
    return "\n".join(parts)


@mcp.tool()
def git_checkout(branch: str, create: bool = False) -> str:
    """Switch branches or create a new branch.

    Args:
        branch: Branch name to check out.
        create: When True, create the branch (-b) before switching.
    """
    if create:
        return run_git("checkout", "-b", branch)
    return run_git("checkout", branch)


@mcp.tool()
def git_branches() -> str:
    """List all local and remote-tracking branches."""
    return run_git("branch", "-a")


@mcp.tool()
def git_push(remote: str = "origin", branch: str = "") -> str:
    """Push commits to a remote.

    Args:
        remote: Remote name.
        branch: Branch to push; leave empty for default.
    """
    args = ["push", remote]
    if branch:
        args.append(branch)
    return run_git(*args)


@mcp.tool()
def git_pull(remote: str = "origin", branch: str = "") -> str:
    """Pull from a remote.

    Args:
        remote: Remote name.
        branch: Branch to pull; leave empty for default.
    """
    args = ["pull", remote]
    if branch:
        args.append(branch)
    return run_git(*args)


@mcp.tool()
def gh_pr_create(title: str, body: str = "", base: str = "main") -> str:
    """Create a GitHub pull request for the current branch (requires gh CLI).

    Args:
        title: PR title.
        body: PR description (markdown).
        base: Base branch name.
    """
    cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    result = subprocess.run(cmd, cwd=DEFAULT_CWD, capture_output=True, text=True)
    return result.stdout + result.stderr

mcp.run(transport="stdio")