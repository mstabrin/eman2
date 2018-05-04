# Find Boost
set(Boost_USE_MULTITHREADED ON)
set(Boost_NO_BOOST_CMAKE ON)
find_package(Boost COMPONENTS python REQUIRED)

message("Boost_LIBRARIES:   ${Boost_LIBRARIES}")
message("Boost_INCLUDE_DIR: ${Boost_INCLUDE_DIR}")

#this definition is for boost.python > 1.35.0 
set_target_properties(Boost::python
					  PROPERTIES
					  INTERFACE_COMPILE_DEFINITIONS BOOST_PYTHON_NO_PY_SIGNATURES
					  INTERFACE_LINK_LIBRARIES Python::Python
					  )
if(WIN32)
	ADD_DEFINITIONS(-DBOOST_DISABLE_ASSERTS)
endif()

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
	
	target_link_libraries(${libname} EM2 Boost::python)
	install(TARGETS ${libname} DESTINATION ${SP_DIR})
endfunction()

#	ADD_PYSTE_LIB(pyGLUtils2)
	ADD_PYSTE_LIB(pyMarchingCubes2)
	
	target_sources(pyMarchingCubes2 PRIVATE
				   ${CMAKE_SOURCE_DIR}/libEM/marchingcubes.cpp
				   )
#	target_sources(pyGLUtils2 PRIVATE
#				   ${CMAKE_SOURCE_DIR}/libEM/emftgl.cpp
#				   ${CMAKE_SOURCE_DIR}/libEM/glutil.cpp
#				   )
	target_link_libraries(pyMarchingCubes2 OpenGL::OpenGL)
#	target_link_libraries(pyGLUtils2       pyMarchingCubes2 FTGL::FTGL)
	target_include_directories(pyMarchingCubes2
    PUBLIC /usr/include
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
	get_target_property(prop_opengl_inc           OpenGL::OpenGL   INTERFACE_INCLUDE_DIRECTORIES)
	get_target_property(prop_opengl_inc_interface OpenGL::OpenGL   INTERFACE_INCLUDE_DIRECTORIES)

	message_var(prop_opengl_inc)
	message_var(prop_opengl_inc_interface)

	message_var(prop_march_inc)
	message_var(prop_march_inc_interface)
	message_var(prop_march_lib)
