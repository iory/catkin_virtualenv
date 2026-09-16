#!/usr/bin/env python
# Software License Agreement (GPL)
#
# \file      venv.py
# \authors   Paul Bovbel <pbovbel@locusrobotics.com>
# \copyright Copyright (c) (2017,), Locus Robotics, All rights reserved.
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import difflib
import logging
import os
import re
import shutil

from . import run_command
from .collect_requirements import collect_requirements

_BYTECODE_REGEX = re.compile(r".*\.py[co]")
_COMMENT_REGEX = re.compile(r"(^|\s+)#.*$", flags=re.MULTILINE)

logger = logging.getLogger(__name__)


def find_uv(uv):
    """Resolve the uv executable.

    Parameters
    ----------
    uv : str
        Path of the uv executable, normally the one bundled with catkin_virtualenv.

    Returns
    -------
    str
        Absolute path to the uv executable.
    """
    uv_executable = shutil.which(uv)
    if uv_executable is None:
        raise RuntimeError("uv executable {} does not exist or is not executable.".format(uv))
    return os.path.abspath(uv_executable)


class Virtualenv:
    def __init__(self, path, uv):
        """Manage a uv-created virtualenv at the specified path."""
        self.path = path
        self.uv = find_uv(uv)

    def initialize(self, python, use_system_packages, clean=True):
        """Initialize a new relocatable virtualenv using the specified python interpreter."""
        if clean and os.path.exists(self.path):
            shutil.rmtree(self.path)

        # Resolve the interpreter ourselves: given a bare name such as 'python3', uv would prefer a uv-managed
        # python over the system one, and ROS packages must run against the system interpreter.
        system_python = shutil.which(python)
        if not system_python:
            error_msg = "Unable to find a system-installed {}.".format(python)
            if python and python[0].isdigit():
                error_msg += " Perhaps you meant python{}".format(python)
            raise RuntimeError(error_msg)

        # --relocatable makes entrypoints and activation scripts path-independent, so the venv can be copied
        # into the devel and install spaces as-is.
        command = [self.uv, "venv", "--relocatable", "--python", system_python]
        if use_system_packages:
            command.append("--system-site-packages")
        command.append(self.path)
        run_command(command, check=True)

    def install(self, requirements, extra_uv_args):
        """Sync a virtualenv with the specified requirements."""
        command = [self.uv, "pip", "install", "--python", self._venv_bin("python")] + extra_uv_args
        # Install one file at a time so that later requirements (i.e. this package's) override inherited ones.
        for req in requirements:
            run_command(command + ["-r", req], check=True)

    def check(self, requirements, extra_uv_args, extra_uv_compile_args=()):
        """Check if a set of requirements is completely locked."""
        with open(requirements, "r") as f:
            existing_requirements = f.read()

        # Re-lock the requirements
        command = self._compile_command(requirements, extra_uv_args, extra_uv_compile_args)
        result = run_command(command, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError("Failed to re-lock {}:\n{}".format(requirements, result.stderr.decode()))
        generated_requirements = result.stdout.decode()

        def _format(content):
            # Remove comments
            content = _COMMENT_REGEX.sub("", content)
            # Remove case sensitivity
            content = content.lower()
            # Split into lines for diff, dropping blank lines
            content = [line.strip() for line in content.splitlines() if line.strip()]
            # ignore order
            content.sort()
            return content

        # Compare against existing requirements
        diff = list(difflib.unified_diff(_format(existing_requirements), _format(generated_requirements)))

        return diff

    def lock(self, package_name, input_requirements, no_overwrite, extra_uv_args, extra_uv_compile_args=(),
             variant=None):
        """Create a frozen requirement set from a set of input specifications."""
        try:
            output_requirements = collect_requirements(package_name, no_deps=True, variant=variant)[0]
        except IndexError:
            logger.info("Package doesn't export any requirements, step can be skipped")
            return

        if no_overwrite and os.path.exists(output_requirements):
            logger.info("Lock file already exists, not overwriting")
            return

        if os.path.normpath(input_requirements) == os.path.normpath(output_requirements):
            raise RuntimeError(
                "Trying to write locked requirements {} into a path specified as input: {}".format(
                    output_requirements, input_requirements
                )
            )

        command = self._compile_command(input_requirements, extra_uv_args, extra_uv_compile_args) + ["-o", output_requirements]
        run_command(command, check=True)

        logger.info("Wrote new lock file to {}".format(output_requirements))

    def relocate(self):
        """Prepare a copied virtualenv for its final location."""
        # The venv itself is created with --relocatable, only bytecode still embeds absolute paths.
        self._delete_bytecode()

    def _compile_command(self, requirements, extra_uv_args, extra_uv_compile_args=()):
        # Resolve against the venv's interpreter so environment markers match the python in use.
        return [
            self.uv,
            "pip",
            "compile",
            "--quiet",
            "--no-header",
            "--annotation-style",
            "line",
            "--python",
            self._venv_bin("python"),
        ] + list(extra_uv_args) + list(extra_uv_compile_args) + [requirements]

    def _venv_bin(self, binary_name):
        binary_path = os.path.join(self.path, "bin", binary_name)
        if os.path.exists(binary_path):
            return os.path.abspath(binary_path)
        raise RuntimeError("Binary {} not found in venv {}".format(binary_name, self.path))

    def _delete_bytecode(self):
        """Remove all .py[co] files since they embed absolute paths."""
        for root, _, files in os.walk(self.path):
            for f in files:
                if _BYTECODE_REGEX.match(f):
                    os.remove(os.path.join(root, f))
