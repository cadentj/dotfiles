## python

Reasoning behind decisions:

- Adopt as many `uv init` defaults as possible, e.g., py.typed by default.

- `_internal` directory to encourage no public API by default.  Hopefully
  induce LLM to be willing to do refactors without leaving BC shims lying
  around.

- Build system: hatchling.  uv default.  We do want a build backend so that
  CLI tool invocation works.

- Python version: the latest.  If uv is managing your Python install for a CLI
  there's no reason not to use the latest Python, UNLESS you have a dependency
  that specifically needs something earlier.  (Library would make different
  decision here.)

- Version bounds on built-in dependencies: latest possible, because that is
  the 'uv add' default.  We will need to occasionally rev these though.

- `--tb=native` on pytest by default because the default pytest backtraces
  are overly long and blow out your model's context.  Actually there is
  probably more improvement for the pytest output formatting possible here.

Some especially controversial decisions:

- `pytest-xdist` is enabled by default.  This is a huge QoL improvement as
  your tests run a lot faster but you need to actually have tests that are
  parallel-safe, which will be hit-or-miss with a model, and there won't be a
  clear signal when you've messed up as it will be nondeterministically
  failing tests (the worst kind).  It's easiest to enforce that running tests
  in parallel is safe early in the project though, so we think the payoff is
  worth it, especially since you can ask the LLM to rewrite code that is not
  parallel safe to be parallel safe.
