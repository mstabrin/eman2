function(ADD_PYSTE_LIB libname)
	add_library(${libname} SHARED lib${libname}.cpp)
	
	if(WIN32)
		set(suffix .pyd)
	else()
		set(suffix .so)
	endif()

	set_target_properties(${libname}
			PROPERTIES
			PREFIX lib
			SUFFIX ${suffix}
			)
	
endfunction()

	ADD_PYSTE_LIB(pyMarchingCubes2)
	
	target_sources(pyMarchingCubes2 PRIVATE
				   marchingcubes.cpp
				   )
	target_include_directories(pyMarchingCubes2
    PRIVATE "/usr/include"
#OpenGL::OpenGL
#        $<INSTALL_INTERFACE:include>    
#        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
#        OpenGL::OpenGL
#    PRIVATE
#        ${CMAKE_CURRENT_SOURCE_DIR}/src
)
	
	get_target_property(prop_march_inc            pyMarchingCubes2 INCLUDE_DIRECTORIES)
	get_target_property(prop_march_inc_interface  pyMarchingCubes2 INTERFACE_INCLUDE_DIRECTORIES)
	get_target_property(prop_march_lib            pyMarchingCubes2 INTERFACE_LINK_LIBRARIES)
#	get_target_property(prop_opengl_inc           OpenGL::OpenGL   INTERFACE_INCLUDE_DIRECTORIES)
#	get_target_property(prop_opengl_inc_interface OpenGL::OpenGL   INTERFACE_INCLUDE_DIRECTORIES)

	message_var(prop_opengl_inc)
	message_var(prop_opengl_inc_interface)

	message_var(prop_march_inc)
	message_var(prop_march_inc_interface)
	message_var(prop_march_lib)
