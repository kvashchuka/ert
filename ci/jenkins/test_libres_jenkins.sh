#!/bin/bash
set -x
# This script is designed to be able to run in stages in the Jenkins pipline
#
# You can also run it locally. Note that only the committed code is tested,
# not changes in your working directory.
#
# If you want to run the whole build in one go:
#   sh testjenkins.sh build_and_test
#
# If you want to run the build in separate stages:
#   sh testjenkins.sh setup
#   sh testjenkins.sh build_elc
#   etc...
#
# By default it will try to build everything inside a folder 'jenkinsbuild'
# You can override this with the env variable WORKING_DIR e.g.:
#   WORKING_DIR=$(mktemp -d) sh testjenkins.sh build_and_test
#
# After https://github.com/equinor/ert/issues/1634 the ERT_SOURCE_ROOT needs to
# point at the ert source root (where .git is).

build_and_test () {
	rm -rf jenkinsbuild
	mkdir jenkinsbuild
	run setup
	run build_libecl
	run build_libres
	run build_res
	run run_ctest
	run run_pytest_normal
	run run_pytest_equinor
}

setup () {
	run setup_variables
	run create_directories
	run create_virtualenv
	run source_build_tools
	run clone_repos
}

build_libecl () {
	run enable_environment

	pushd $LIBECL_BUILD
	cmake .. -DCMAKE_INSTALL_PREFIX=$INSTALL
	make -j 6 install
	popd
}

build_libres () {
	run enable_environment

	pushd $LIBRES_BUILD
	cmake ${ERT_SOURCE_ROOT}/libres \
		  -DCMAKE_PREFIX_PATH=$INSTALL \
		  -DCMAKE_INSTALL_PREFIX=$INSTALL \
		  -DBUILD_TESTS=ON \
		  -DEQUINOR_TESTDATA_ROOT=/project/res-testdata/ErtTestData
	make -j 6 install
	popd
}

build_res () {
	run enable_environment
	pip install ${ERT_SOURCE_ROOT}
	pip install -r dev-requirements.txt
}

source_build_tools() {
	export PATH=/opt/rh/devtoolset-8/root/bin:$PATH
	python --version
	gcc --version
	cmake --version

	set -e
}

setup_variables () {
	ENV=$WORKING_DIR/venv
	INSTALL=$WORKING_DIR/install

	LIBECL_ROOT=$WORKING_DIR/libecl
	LIBECL_BUILD=$LIBECL_ROOT/build

	LIBRES_ROOT=$WORKING_DIR/_libres
	LIBRES_BUILD=$LIBRES_ROOT/build
}

enable_environment () {
	run setup_variables
	source $ENV/bin/activate
	run source_build_tools

	export ERT_SHOW_BACKTRACE=Y
	export RMS_SITE_CONFIG=/prog/res/komodo/bleeding-py36-rhel7/root/lib/python3.6/site-packages/ert_configurations/resources/rms_config.yml
}

create_directories () {
	mkdir $INSTALL
}

clone_repos () {
	echo "Cloning into $LIBECL_ROOT"
	git clone https://github.com/equinor/libecl $LIBECL_ROOT
	mkdir -p $LIBECL_BUILD

	echo "Cloning into $LIBRES_ROOT"
	git clone . $LIBRES_ROOT
	mkdir -p $LIBRES_BUILD
	ln -s /project/res-testdata/ErtTestData $LIBRES_ROOT/../test-data/Equinor
}

create_virtualenv () {
	mkdir $ENV
	python3 -m venv $ENV
	source $ENV/bin/activate
	pip install -U pip wheel setuptools cmake
}

run_ctest () {
	run enable_environment
	pushd $LIBRES_BUILD
	export ERT_SITE_CONFIG=${ERT_SOURCE_ROOT}/share/ert/site-config
	ctest -j $CTEST_JARG -E Lint --output-on-failure
	popd
}

run_pytest_normal () {
	run enable_environment

	# Avoid implicitly loaded cwd modules
	pushd ${LIBRES_BUILD}
	python -m pytest -m "not equinor_test" --durations=10 ${ERT_SOURCE_ROOT}/libres/tests
	popd
}


run_pytest_equinor () {
	ln -s /project/res-testdata/ErtTestData ${ERT_SOURCE_ROOT}/test-data/Equinor
	run enable_environment

	# Avoid implicitly loaded cwd modules
	pushd ${LIBRES_BUILD}
	python -m pytest -m "equinor_test" --durations=10 ${ERT_SOURCE_ROOT}/libres/tests
	popd
}


run () {
	echo ""
	echo "----- Running step: $1 -----"
	echo ""
	$1

	echo ""
	echo "----- $1 finished -----"
	echo ""
}

if [ -z "$CTEST_JARG" ]
	then
		CTEST_JARG="6"
fi

if [ -z "$WORKING_DIR" ]
	then
		WORKING_DIR=$(pwd)/jenkinsbuild
		ERT_SOURCE_ROOT=$(pwd)
	else
		ERT_SOURCE_ROOT=${WORKING_DIR}
fi

if [ $# -ne 0 ]
	then
		run $1
fi
