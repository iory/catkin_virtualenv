cmake_minimum_required(VERSION 3.5.1)
project(catkin_virtualenv)

find_package(catkin REQUIRED)

catkin_package(CFG_EXTRAS ${PROJECT_NAME}-extras.cmake)

catkin_python_setup()

# Bundle uv at a pinned version so that every package builds its virtualenv with the same uv, without requiring
# it to be installed on the system. The version is part of the path so that bumping it re-downloads uv.
set(uv_version 0.12.14)
set(uv_bootstrap_dir ${CMAKE_CURRENT_BINARY_DIR}/uv-${uv_version})
set(uv_devel_executable ${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_BIN_DESTINATION}/uv)

add_custom_command(COMMENT "Download uv ${uv_version}"
  OUTPUT ${uv_bootstrap_dir}/bin/uv
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${uv_bootstrap_dir}
  COMMAND ${PYTHON_EXECUTABLE} -m venv ${uv_bootstrap_dir}
  COMMAND ${uv_bootstrap_dir}/bin/python -m pip install --quiet --disable-pip-version-check --only-binary=:all:
    uv==${uv_version}
)

add_custom_command(COMMENT "Copy uv ${uv_version} to devel space"
  OUTPUT ${uv_devel_executable}
  COMMAND ${CMAKE_COMMAND} -E copy ${uv_bootstrap_dir}/bin/uv ${uv_devel_executable}
  DEPENDS ${uv_bootstrap_dir}/bin/uv
)

add_custom_target(${PROJECT_NAME}_uv ALL DEPENDS ${uv_devel_executable})

install(PROGRAMS ${uv_bootstrap_dir}/bin/uv
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY cmake
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  PATTERN ${PROJECT_NAME}-extras.cmake* EXCLUDE
)

set(python_scripts
  scripts/collect_requirements
  scripts/venv_init
  scripts/venv_check
  scripts/venv_lock
  scripts/venv_install
  scripts/venv_relocate
)

catkin_install_python(PROGRAMS ${python_scripts}
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(FILES requirements.txt
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

if(CATKIN_ENABLE_TESTING)
  find_package(roslint REQUIRED)
  roslint_python()
  roslint_python(${python_scripts})
  roslint_add_test()
endif()
