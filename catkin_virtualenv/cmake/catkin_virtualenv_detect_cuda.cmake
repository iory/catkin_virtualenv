# Software License Agreement (GPL)
#
# \file      catkin_virtualenv_detect_cuda.cmake
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

# catkin_virtualenv_detect_cuda(<output variable>)
#
# Set the variable to TRUE when this machine has an NVIDIA GPU with a working driver (nvidia-smi lists a
# GPU), FALSE otherwise, so that a package can lock and install e.g. a CPU-only torch without a GPU:
#
#   catkin_virtualenv_detect_cuda(has_cuda)
#   if(NOT has_cuda)
#     set(torch_args REQUIREMENTS_VARIANT cpu EXTRA_UV_ARGS --torch-backend cpu)
#   endif()
#   catkin_generate_virtualenv(INPUT_REQUIREMENTS requirements.in ${torch_args})
#
# The cache variable CATKIN_VIRTUALENV_CUDA (ON or OFF) overrides the detection, e.g. to build the CUDA
# variant on a machine whose GPU is used only later.
function(catkin_virtualenv_detect_cuda output)
  if(DEFINED CATKIN_VIRTUALENV_CUDA AND NOT CATKIN_VIRTUALENV_CUDA STREQUAL "")
    if(CATKIN_VIRTUALENV_CUDA)
      set(${output} TRUE PARENT_SCOPE)
    else()
      set(${output} FALSE PARENT_SCOPE)
    endif()
    message(STATUS "CUDA ${CATKIN_VIRTUALENV_CUDA} (CATKIN_VIRTUALENV_CUDA)")
    return()
  endif()

  find_program(nvidia_smi nvidia-smi)
  set(has_cuda FALSE)
  if(nvidia_smi)
    execute_process(COMMAND ${nvidia_smi} -L
      RESULT_VARIABLE result OUTPUT_VARIABLE gpus ERROR_QUIET OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(result EQUAL 0 AND gpus MATCHES "GPU")
      set(has_cuda TRUE)
    endif()
  endif()
  if(has_cuda)
    message(STATUS "CUDA found: ${gpus}")
  else()
    message(STATUS "CUDA not found (no GPU listed by nvidia-smi)")
  endif()
  set(${output} ${has_cuda} PARENT_SCOPE)
endfunction()
