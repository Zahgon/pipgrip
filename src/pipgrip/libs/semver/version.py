# BSD 3-Clause License
#
# Copyright (c) 2020 - 2024, ddelange, <ddelange@delange.dev>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause
# flake8: noqa:A003
import hashlib
import re
from typing import List, Optional, Union

from pipgrip.libs.semver.empty_constraint import EmptyConstraint
from pipgrip.libs.semver.exceptions import ParseVersionError
from pipgrip.libs.semver.patterns import COMPLETE_VERSION
from pipgrip.libs.semver.version_constraint import VersionConstraint
from pipgrip.libs.semver.version_range import VersionRange
from pipgrip.libs.semver.version_union import VersionUnion


class Version(VersionRange):
    """
    A parsed semantic version number.
    """

    def __init__(
        self,
        major,  # type: int
        minor=None,  # type: Optional[int]
        patch=None,  # type: Optional[int]
        rest=None,  # type: Optional[int]
        pre=None,  # type: Optional[str]
        build=None,  # type: Optional[str]
        text=None,  # type: Optional[str]
        precision=None,  # type: Optional[int]
    ):  # type: (...) -> None
        self._major = int(major)
        self._precision = None
        if precision is None:
            self._precision = 1

        if minor is None:
            minor = 0
        else:
            if self._precision is not None:
                self._precision += 1

        self._minor = int(minor)

        if patch is None:
            patch = 0
        else:
            if self._precision is not None:
                self._precision += 1

        if rest is None:
            rest = 0
        else:
            if self._precision is not None:
                self._precision += 1

        if precision is not None:
            self._precision = precision

        self._patch = int(patch)
        self._rest = int(rest)

        if text is None:
            parts = [str(major)]
            if self._precision >= 2 or minor != 0:
                parts.append(str(minor))

                if self._precision >= 3 or patch != 0:
                    parts.append(str(patch))

                if self._precision >= 4 or rest != 0:
                    parts.append(str(rest))

            text = ".".join(parts)
            if pre:
                text += "-{}".format(pre)

            if build:
                text += "+{}".format(build)

        self._text = text

        pre = self._normalize_prerelease(pre)

        self._prerelease = []
        if pre is not None:
            self._prerelease = self._split_parts(pre)

        build = self._normalize_build(build)

        self._build = []
        if build is not None:
            if build.startswith(("-", "+")):
                build = build[1:]

            self._build = self._split_parts(build)




















    @classmethod
    def parse(cls, text):  # type: (str) -> Version
        # fmt: off
        if not isinstance(text, ("".__class__, u"".__class__)):
            raise ParseVersionError('Unable to parse "{}".'.format(text))
        # fmt: on

        try:
            match = COMPLETE_VERSION.match(text)
        except TypeError:
            match = None

        if match is None:
            # VCS support: use numerical hash
            match = COMPLETE_VERSION.match(
                str(int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % 10**12)
            )

        text = text.rstrip(".")

        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else None
        patch = int(match.group(3)) if match.group(3) else None
        rest = int(match.group(4)) if match.group(4) else None

        pre = match.group(5)
        build = match.group(6)

        if build:
            build = build.lstrip("+")

        return Version(major, minor, patch, rest, pre, build, text)

    def is_vcs(self):  # type: () -> bool
        return str(self._major) not in self._text

    def is_any(self):  # type: () -> bool
        return False

    def is_empty(self):  # type: () -> bool
        return False

    def is_prerelease(self):  # type: () -> bool
        return len(self._prerelease) > 0

    def allows(self, version):  # type: (Version) -> bool
        return self == version

    def allows_all(self, other):  # type: (VersionConstraint) -> bool
        return other.is_empty() or other == self

    def allows_any(self, other):  # type: (VersionConstraint) -> bool
        return other.allows(self)

    def intersect(self, other):  # type: (VersionConstraint) -> VersionConstraint
        if other.allows(self):
            return self

        return EmptyConstraint()

    def union(self, other):  # type: (VersionConstraint) -> VersionConstraint
        from pipgrip.libs.semver.version_range import VersionRange

        if other.allows(self):
            return other

        if isinstance(other, VersionRange):
            if other.min == self:
                return VersionRange(
                    other.min,
                    other.max,
                    include_min=True,
                    include_max=other.include_max,
                )

            if other.max == self:
                return VersionRange(
                    other.min,
                    other.max,
                    include_min=other.include_min,
                    include_max=True,
                )

        return VersionUnion.of(self, other)

    def difference(self, other):  # type: (VersionConstraint) -> VersionConstraint
        if other.allows(self):
            return EmptyConstraint()

        return self

    def equals_without_prerelease(self, other):  # type: (Version) -> bool
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )







    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __ge__(self, other):
        return self._cmp(other) >= 0




    def __eq__(self, other):  # type: (Version) -> bool
        if not isinstance(other, Version):
            return NotImplemented

        return (
            self._major == other.major
            and self._minor == other.minor
            and self._patch == other.patch
            and self._rest == other.rest
            and self._prerelease == other.prerelease
            and self._build == other.build
        )

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self._text

    def __repr__(self):
        return "<Version {}>".format(str(self))

    def __hash__(self):
        return hash(
            (
                self.major,
                self.minor,
                self.patch,
                ".".join(str(p) for p in self.prerelease),
                ".".join(str(p) for p in self.build),
            )
        )
