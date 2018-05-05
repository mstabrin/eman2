add_library(pyA SHARED libpyA.cpp)

set_target_properties(pyA
		PROPERTIES
		PREFIX lib
		SUFFIX .so
		)
	
#INCLUDE_DIRECTORIES("/usr/include")
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -I/usr/include")
set(OPENGL_INCLUDE_DIR /usr/include)
target_sources(pyA PRIVATE
			   A.cpp
			   )
set_target_properties(pyA PROPERTIES
					  INTERFACE_INCLUDE_DIRECTORIES "${OPENGL_INCLUDE_DIR}"
					  INCLUDE_DIRECTORIES "${OPENGL_INCLUDE_DIR}"
#					  INTERFACE_LINK_LIBRARIES      "${OPENGL_LIBRARIES}"
#					  INTERFACE_COMPILE_DEFINITIONS USE_OPENGL
					  )


#target_include_directories(pyA
#    PRIVATE "/usr/include"
#OpenGL::OpenGL
#        $<INSTALL_INTERFACE:include>    
#        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
#        OpenGL::OpenGL
#    PRIVATE
#        ${CMAKE_CURRENT_SOURCE_DIR}/src
#)
	
	get_target_property(prop_march_inc            pyA INCLUDE_DIRECTORIES)
	get_target_property(prop_march_inc_interface  pyA INTERFACE_INCLUDE_DIRECTORIES)
#	get_target_property(prop_march_lib            pyA INTERFACE_LINK_LIBRARIES)
#	get_target_property(prop_opengl_inc           OpenGL::OpenGL   INTERFACE_INCLUDE_DIRECTORIES)
#	get_target_property(prop_opengl_inc_interface OpenGL::OpenGL   INTERFACE_INCLUDE_DIRECTORIES)

#	message(prop_opengl_inc)
#	message(prop_opengl_inc_interface)
#
	message("prop_march_inc:           ${prop_march_inc}")
	message("prop_march_inc_interface: ${prop_march_inc_interface}")
#	message("prop_march_lib:           ${prop_march_lib}")
