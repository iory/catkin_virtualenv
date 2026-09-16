#!/usr/bin/env python
# Software License Agreement (GPL)
#
# \file      collect_requirements.py
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
from __future__ import print_function

import distro
import logging
import os

from queue import Queue
from catkin.find_in_workspaces import find_in_workspaces
from catkin_pkg.package import parse_package


CATKIN_VIRTUALENV_TAGNAME = "pip_requirements"

logger = logging.getLogger(__name__)


def _with_suffix(path, suffix):
    base, ext = os.path.splitext(path)
    return f"{base}-{suffix}{ext}"


def get_distro_requirements_path(base_requirements_path):
    # type: (str) -> str
    """
    Given a base requirements path (e.g., 'requirements.txt'), return the path to a
    distro-specific requirements file if it exists (e.g., 'requirements-jammy.txt' on Ubuntu Jammy).
    Falls back to the original path if no distro-specific file exists.
    """
    codename = distro.codename().lower()
    if not codename:
        return base_requirements_path

    distro_requirements_path = _with_suffix(base_requirements_path, codename)
    if os.path.exists(distro_requirements_path):
        logger.info(f"Using distro-specific requirements file: {distro_requirements_path}")
        return distro_requirements_path

    return base_requirements_path


def get_requirements_path(base_requirements_path, variant=None, strict=False):
    # type: (str, Optional[str], bool) -> str
    """
    Return the requirements file to use for a base path (e.g., 'requirements.txt').

    With a variant (e.g., 'cpu'), 'requirements-cpu-jammy.txt' or 'requirements-cpu.txt' is used. When
    ``strict`` (the package that owns the virtualenv) the variant file is used even if it does not exist
    yet, since it is the lock file to write; otherwise (inherited requirements) a package without that
    variant falls back to its distro-specific or base file.
    """
    if variant:
        variant_path = _with_suffix(base_requirements_path, variant)
        variant_distro_path = get_distro_requirements_path(variant_path)
        if os.path.exists(variant_distro_path):
            logger.info(f"Using {variant} requirements file: {variant_distro_path}")
            return variant_distro_path
        if strict:
            return variant_path
    return get_distro_requirements_path(base_requirements_path)


def parse_exported_requirements(package, package_dir, variant=None, strict=False):
    # type: (catkin_pkg.package.Package, str, Optional[str], bool) -> List[str]
    requirements_list = []
    for export in package.exports:
        if export.tagname == CATKIN_VIRTUALENV_TAGNAME:
            base_requirements_path = os.path.join(package_dir, export.content)
            requirements_path = get_requirements_path(base_requirements_path, variant, strict)
            requirements_list.append(requirements_path)
    return requirements_list


def process_package(package_name, soft_fail=True, variant=None):
    # type: (str, bool, Optional[str]) -> List[str], List[str]
    try:
        package_path = find_in_workspaces(project=package_name, path="package.xml", first_match_only=True,)[0]
    except IndexError:
        if not soft_fail:
            raise RuntimeError("Unable to process package {}".format(package_name))
        else:
            # This is not a catkin dependency
            return [], []
    else:
        package = parse_package(package_path)
        dependencies = package.build_depends + package.test_depends
        requirements = parse_exported_requirements(
            package, os.path.dirname(package_path), variant=variant, strict=not soft_fail)
        return requirements, dependencies


def collect_requirements(package_name, no_deps=False, variant=None):
    # type: (str, bool, Optional[str]) -> List[str]
    """ Collect requirements inherited by a package, preferring the files of a variant (e.g. 'cpu'). """
    package_queue = Queue()
    package_queue.put(package_name)
    processed_packages = set()
    requirements_list = []

    while not package_queue.empty():
        queued_package = package_queue.get()

        if queued_package not in processed_packages:
            processed_packages.add(queued_package)
            requirements, dependencies = process_package(
                package_name=queued_package, soft_fail=(queued_package != package_name), variant=variant
            )
            requirements_list = requirements + requirements_list

            if not no_deps:
                # Add dependencies in reverse order so that with prepend logic,
                # they end up in declaration order (first declared = installed first)
                for dependency in reversed(dependencies):
                    package_queue.put(dependency.name)

    return requirements_list
