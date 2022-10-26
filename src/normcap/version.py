"""Supposed to be a very simplified drop in replacement for packaging.version.Version.

Mainly implemented to avoid packaging as extra dependency and because complicated
versions are unexepected in the scope of this project.
"""


class Version:
    """Very, very simplified drop in replacement for packaging.version.Version."""

    def __init__(self, version_string: str):
        self.string = version_string.strip()
        self.components = self.string.split(".")
        self.major, self.minor, self.patch, self.rest = self._parse(self.components)

    def _parse(self, components: list):
        major = minor = patch = rest = None
        try:
            major = int(components[0])

            if len(components) > 1:
                minor = int(components[1])
            else:
                minor = 0

            if len(components) > 2:
                patch_part = components[2]
                patch_number = ""
                for c in patch_part:
                    if c.isnumeric():
                        patch_number += c
                    else:
                        break
                patch = int(patch_number)
                rest = patch_part[len(patch_number) :]
            else:
                patch = 0
                rest = ""

        except Exception as e:
            raise ValueError(f"Couldn't parse version string '{self.string}'") from e

        return major, minor, patch, rest

    def __gt__(self, other) -> bool:
        if self.major > other.major:
            return True
        if self.major == other.major:
            if self.minor > other.minor:
                return True
            if self.minor == other.minor:
                if self.patch > other.patch:
                    return True
                if self.patch == other.patch:
                    if self.rest > other.rest or (self.rest == "" and other.rest != ""):
                        return True
        return False

    def __eq__(self, other) -> bool:
        return (
            (self.major == other.major)
            and (self.minor == other.minor)
            and (self.patch == other.patch)
            and (self.rest == other.rest)
        )

    def __ge__(self, other) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __str__(self) -> str:
        return str(".".join(self.components))

    def __repr__(self) -> str:
        return f"<Version('{self}')>"
