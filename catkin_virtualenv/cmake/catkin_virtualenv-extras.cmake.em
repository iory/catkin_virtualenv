@[if DEVELSPACE]@
set(@(PROJECT_NAME)_CMAKE_DIR @(CMAKE_CURRENT_SOURCE_DIR)/cmake)
set(@(PROJECT_NAME)_UV_EXECUTABLE @(CATKIN_DEVEL_PREFIX)/@(CATKIN_PACKAGE_BIN_DESTINATION)/uv)
@[else]@
set(catkin_virtualenv_CMAKE_DIR ${@(PROJECT_NAME)_DIR})
# ${@(PROJECT_NAME)_DIR} is <prefix>/@(CATKIN_PACKAGE_SHARE_DESTINATION)/cmake
get_filename_component(@(PROJECT_NAME)_UV_EXECUTABLE
  ${@(PROJECT_NAME)_DIR}/../../../@(CATKIN_PACKAGE_BIN_DESTINATION)/uv ABSOLUTE)
@[end if]@

# Include cmake modules from @(PROJECT_NAME)
include(${@(PROJECT_NAME)_CMAKE_DIR}/catkin_generate_virtualenv.cmake)
include(${@(PROJECT_NAME)_CMAKE_DIR}/catkin_install_python.cmake)
