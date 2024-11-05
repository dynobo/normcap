# Use hatch instead poetry

- Status: accepted
- Deciders: @dynobo
- Date: 2024-11-06
- Superseeds: [ADR-005](./005-use-hatch-instead-poetry.md)

## Context and Problem Statement

Currently, [hatch](https://github.com/pypa/hatch) is used for dependency
management & locking, virtual environment management, and building. While in general
this works quite well, there are some reoccurring pain points:

- Misses built-in lock file creation.
- Handling of the `.virtualenvs` is a bit cumbersome:
  - There seems no easy way to update them (which can be forgotten).
  - The env is not super standard, so tools like `direnv` are needed to auto-activate.
- Dependency resolution somewhat slow.

## Decision Drivers

- Maintenance efforts
- Implementation efforts
- Developer experience

## Considered Options

### (A) Do nothing.

Stay with [hatch](https://github.com/pypa/hatch).

### (B) Switch to [uv](https://docs.astral.sh/uv/)

As uv (at the moment) misses task running capabilities, it would need to be complemented
by a task runner like [poe](https://github.com/nat-n/poethepoet).

### (C) Previous options

See options in [ADR-005](./005-use-hatch-instead-poetry.md).

## Decision Outcome

**Chosen option: (D) Switch to hatch.**

### Positive Consequences

- Better developer experience.
- Faster in CICD.
- Official github action support.
- Handles Python versions as well (useful for debugging and testing).

### Negative Consequences

- Increases complexity a bit due to the need for an extra task runner (but uv
  might receive this feature in future).
- Implementation effort for transition.

### Neutral

- Still requires `hatchling` as build backend. This allows to still use the custom
  build-hook.

## Pros and Cons of the Options

### (A) Do nothing

- Good, because less implementation effort.
- Good, as it offers a single entrypoint for tasks.
- Neutral, as dependency locking is currently not PEP compliant and therefore not
  integrate into `hatch` core. However, this is subject to change, and until it is
  change the 3rd party plugin
  [hatch-pip-deepfreeze](https://github.com/sbidoul/hatch-pip-deepfreeze) could be
  used.
- Bad, because it's not widely known which might be a barrier for contributors.
- Bad, because the dependency resolution slows down a bit.
- Bad, because it is (not yet) as widely adopted and therefore less well integrated.
  E.g. it takes more effort to get the following things to work:
    - Auto-activation of environment in `zsh`.
    - Auto-activation of environment in VSCode.
    - Caching of environments in GitHub actions. (Caching with `poetry` is integrated in
      the official `actions/setup-python`.)
    - Cumbersome updating of virtualenvs by recreation.

### (B) Switch to uv

- Good, because it is already more spread and high adoption rate.
- Good, because it creates standard `.venv` which has good integration support (e.g.
  `zsh`, VSCode, GitHub actions).
- Good, because integration receives a lot of attention (e.g. official github action for
  setup).
- Good, because no need to recreate venv due to `uv sync`.
- Good, because it creates a lock file out of the box.
- Neutral, as it doesn't (yet) include a task runner.
- Neutral, as it is being developed quite fast. This leads to quick improvements, but
  might also require a bit more migration efforts.
- Bad, because of implementation efforts during the transition.

## References

- [ADR-005](./005-use-hatch-instead-poetry.md)
- [PR #669](https://github.com/dynobo/normcap/pull/669)
