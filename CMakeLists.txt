CMAKE_MINIMUM_REQUIRED(VERSION 3.7)
PROJECT(AAA
		VERSION 1
		LANGUAGES CXX
		)

set(CMAKE_VERBOSE_MAKEFILE ON)
OPTION(DEBUG_CMAKE_TARGETS "enable debug output for cmake target properties" ON)
if(DEBUG_CMAKE_TARGETS)
	set(CMAKE_DEBUG_TARGET_PROPERTIES
		INCLUDE_DIRECTORIES
		)
endif()

add_library(libA SHARED a.cpp)

find_package(OpenGL REQUIRED)
message("OPENGL_INCLUDE_DIR: ${OPENGL_INCLUDE_DIR}")

target_sources(libA PRIVATE a.cpp)
set_target_properties(libA PROPERTIES
					  INCLUDE_DIRECTORIES   "${OPENGL_INCLUDE_DIR}/../include;${CMAKE_SOURCE_DIR}/B1"
					  )
