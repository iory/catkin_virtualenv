# Software License Agreement (GPL)
#
# \file      __init__.py
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

import logging
import shlex
import subprocess

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        level=logging.WARNING,
        format='[%(levelname)s] [%(name)s]: %(message)s'
    )
    return logging.getLogger()


def run_command(cmd, *args, **kwargs):
    logger.info(" ".join(cmd))
    if kwargs.pop("capture_output", False):
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    return subprocess.run(cmd, *args, **kwargs)


def parse_extra_args(extra_args):
    """Split the quoted, space-separated argument string that CMake passes through make and the shell.

    Parameters
    ----------
    extra_args : str
        Arguments wrapped in literal double quotes, e.g. '"--index-url https://example.com"'.

    Returns
    -------
    list of str
        Individual arguments.
    """
    return shlex.split(extra_args[1:-1])
