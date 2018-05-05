CMAKE_MINIMUM_REQUIRED(VERSION 3.7)
PROJECT(AAA
		VERSION 1
		LANGUAGES CXX
		)

OPTION(CMAKE_VERBOSE_MAKEFILE "verbose Makefile" ON)
OPTION(DEBUG_CMAKE_TARGETS "enable debug output for cmake target properties" ON)
if(DEBUG_CMAKE_TARGETS)
	set(CMAKE_DEBUG_TARGET_PROPERTIES
		INCLUDE_DIRECTORIES
		COMPILE_DEFINITIONS
		POSITION_INDEPENDENT_CODE
		CONTAINER_SIZE_REQUIRED
		LIB_VERSION
		)
endif()

add_library(libA SHARED A.cpp)

find_package(OpenGL REQUIRED)
message("OPENGL_INCLUDE_DIR: ${OPENGL_INCLUDE_DIR}")
#set(MY_INCLUDE_DIR "${CMAKE_SYSROOT}/usr/include;${CMAKE_SOURCE_DIR}/dir1")
set(MY_INCLUDE_DIR "${OPENGL_INCLUDE_DIR}/../include;${CMAKE_SOURCE_DIR}/dir1")
target_sources(libA PRIVATE
			   A.cpp
			   )
set_target_properties(libA PROPERTIES
#					  INTERFACE_INCLUDE_DIRECTORIES "${MY_INCLUDE_DIR};/usr/include"
					  INCLUDE_DIRECTORIES           "${MY_INCLUDE_DIR}"
#					  INTERFACE_LINK_LIBRARIES      "${OPENGL_LIBRARIES}"
#					  INTERFACE_COMPILE_DEFINITIONS USE_OPENGL
					  )

	
get_target_property(prop_march_inc            libA INCLUDE_DIRECTORIES)
get_target_property(prop_march_inc_interface  libA INTERFACE_INCLUDE_DIRECTORIES)

message("prop_march_inc:           ${prop_march_inc}")
message("prop_march_inc_interface: ${prop_march_inc_interface}")

get_property(incA TARGET libA PROPERTY INCLUDE_DIRECTORIES)
message("incA:")
message("${incA}")


get_property(incA1 TARGET libA PROPERTY INTERFACE_INCLUDE_DIRECTORIES)
message("incA1:")
message("${incA1}")
