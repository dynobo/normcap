# Use hatch instead poetry

- Status: accepted
- Deciders: @dynobo
- Date: 2023-10-27

## Context and Problem Statement

Currently, [poetry](https://github.com/python-poetry/poetry) is used for dependency
management & locking, virtual environment management, and building. While in general
this works quite well, there are some reoccurring pain points:

- The scripting capabilities
  [are limited](https://python-poetry.org/docs/pyproject#scripts).
    - This led to duplicate implementations of tasks like formatting, linting, testing and
      l10n for pre-commit hooks and for the GitHub actions.
    - There are currently multiple entry points for various different tasks, e.g. Python
      package (`poetry build`), Briefcase package (`/bundle/build.py`, babel
      (`l10n.py`), running normcap (script `normcap`), which increases cognitive
      overhead.
- Dependency resolution can be quite slow
- Poetry does not follow PEP standards (however, no problem so far)

## Decision Drivers

- Maintenance efforts
- Complexity reduction
- Implementation efforts

## Considered Options

### (A) Do nothing.

Stay with [poetry](https://github.com/python-poetry/poetry).

### (B) Keep using [poetry](https://github.com/python-poetry/poetry) and combine it with a task-runner like [nox](https://github.com/wntrblm/nox)

### (C) Switch to [nox](https://github.com/wntrblm/nox) and script tasks like building

Scripts should use builtin Python's tools for building and virtual environment
management, otherwise complexity would not be reduced.

### (D) Switch to [hatch](https://github.com/pypa/hatch)

## Decision Outcome

**Chosen option: (D) Switch to hatch.**

### Positive Consequences

- Reduced complexity:
    - Use `hatch` as _one_ tool for most tasks `poetry` supported _as well as_ simple task
      runner.
    - Single entrypoint to tasks (`hatch run ...`)
- Less maintenance effort because of less duplicated code for tasks.
- `hatch` was adopted by PyPA and therefore is future-proof and well-supported.
- Testing a new tool (learning opportunity).

### Negative Consequences

- Implementation effort for transition.
- Some integration efforts (e.g. venv activation via
  [direnv](https://github.com/direnv/direnv) with 3rd party `layout hatch` to be used
  in `zsh` and VSCode). Hopefully, this situation will improve over the time!
- New tool (learning efforts).

### Neutral

- `hatch` does not yet support dependency locking. This is a minor issue, because:
    - A locking feature might be added to `hatch` in midterm (needs some PEP-work, which
      already started).
    - Freezing is supported via 3rd party plugin
      [hatch-pip-deepfreeze](https://github.com/sbidoul/hatch-pip-deepfreeze).
    - In NormCap, currently the only dependencies are `PySide6` & `shiboken6`. They are
      pinned to specific versions anyway and don't have any child-dependencies
      themselves.
    - For development dependencies this is an issue, but the impact of potential problems
      is minor.
- It's unclear, if the scripting support is good enough to ease all required tasks.
    - If this _is_ the case, it would be a positive consequence, as more powerful tools
      like `nox` would bring in more complexity and onboarding efforts.
    - If this is _not_ the case, then it would have negative consequences, because the
      complexity would again grow because of workarounds or bringing in a task runner as
      additional tool.

## Pros and Cons of the Options

### (A) Do nothing

- Good, because less implementation effort.
- Good, because dependency locking grantees coherent development environment and stable
  builds.
- Good, because it is widely spread and therefore has good integration support (e.g.
  `zsh`, VSCode, GitHub actions).
- Bad, because more maintenance effort of duplicate coded tasks.
- Bad, because it requires more cognitive load for running tasks through multiple
  entrypoints.
- Bad, because the slow dependency resolution slows down a bit.

### (B) Keep using poetry and combine it with a task-runner like nox

**Note:** `nox` is just _one_ exemplary (and very promising) task runner. The arguments
below very likely apply to similar tools as well.

- Good, because it covers all required feature very well.
- Good, because the scripting capabilities are great and might be a good option to unify
  the available scripts (`l10.py`, `/bundle/..`).
- Bad, because more tools mean more complexity.
- Bad, because the slow dependency resolution still slows down a bit.
- Bad, because of implementation efforts of migrating the tasks to nox.

### (C) Switch to nox and script tasks like building

**Note:** Tasks that are _not_ integrated in `nox` and should be implemented using
Python standard toolings to have a good development workflow (Dependency management,
Virtual environment management, Building).

**Note:** Another option would be to do leave dependency & and venv management to the
individual developer. (For building, this is probably not a good idea.)

- Good, as it should cover and ease _all_ task scripting activities (l10n, briefcase
  bundles, linting, etc.)
- Good, as it offers a single entrypoint for tasks (if all are scripted!).
- Bad, because it might mean re-implementing tasks which other tools already do quite
  well, or relying on the individual developers to do the right things.

### (D) Switch to hatch

- Good, as its strict standard compliance might make it easier to also use other build
  tools. (NormCap, doesn't really benefit from this.)
- Good, as it offers a single entrypoint for tasks.
- Neutral, as dependency locking is currently not PEP compliant and therefore not
  integrate into `hatch` core. However, this is subject to change, and until it is
  change the 3rd party plugin
  [hatch-pip-deepfreeze](https://github.com/sbidoul/hatch-pip-deepfreeze) could be
  used.
- Neutral, as it has better scripting capabilities than `poetry`, but is way less
  flexible than task runners like `nox`. Currently, it is unclear, if those
  capabilities are really needed.
- Bad, because of implementation efforts during the transition.
- Bad, because it is (not yet) as widely adopted and therefore less well integrated.
  E.g. it takes more effort to get the following things to work:
    - Auto-activation of environment in `zsh`.
    - Auto-activation of environment in VSCode.
    - Caching of environments in GitHub actions. (Caching with `poetry` is integrated in
      the official `actions/setup-python`.)

## References

- [Issue #527](https://github.com/dynobo/normcap/issues/527)
- [PR #549](https://github.com/dynobo/normcap/pull/549)
