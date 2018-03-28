find_program(PYTEST_EXECUTABLE pytest
		PATHS ${CONDA_PREFIX}/bin ${CONDA_PREFIX}/Scripts ENV PATH
		)

find_file(PYTEST_QT  plugin.py ${SP_DIR}/pytestqt)
find_file(PYTEST_COV plugin.py ${SP_DIR}/pytest_cov)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(PyTest
		REQUIRED_VARS PYTEST_EXECUTABLE PYTEST_QT PYTEST_COV
		)
