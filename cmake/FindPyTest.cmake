find_program(PYTEST_EXECUTABLE pytest
		PATHS ${CONDA_PREFIX}/bin ${CONDA_PREFIX}/Scripts ENV PATH
		)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(PyTest
		REQUIRED_VARS PYTEST_EXECUTABLE
		)
