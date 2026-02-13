.SILENT: ;

#Project name (CHANGE THIS)
PROJECT_NAME		= Heat2D_PlaceV2

# Project Variables
PROJECT_DIR			:= $(shell pwd)
BUILD_DIR			= $(PROJECT_DIR)/build
LIB_DIR				= $(PROJECT_DIR)/lib
DEPS_DIR			= $(PROJECT_DIR)/deps
BIN_DIR				= $(PROJECT_DIR)/bin
SRC_INCLUDE			= -I$(PROJECT_DIR)/src


# MASS
MASS_VERSION = develop # Choose a tag(version)/branch/commit to use
MASS_GIT_URL = https://bitbucket.org/mass_library_developers/mass_cuda_core.git
MASS_DIR = $(LIB_DIR)/mass
MASS_REPO = $(MASS_DIR)/mass_repo
# MASS_INCLUDE = -I$(MASS_REPO)/include # Include boost as aregular include directory
MASS_INCLUDE = -isystem $(MASS_REPO)/include # Include boost as a system include directory (suppresses warnings)
MASS_LIBS = $(MASS_REPO)/libs/*.a

## MASS Config
MASS_MAX_AGENTS		= 1
MASS_MAX_NEIGHBORS	= 4
MASS_MAX_DIMS		= 2
MASS_N_DESTINATIONS	= 8
# If you want to use a specific block size, change this value, and add -DBLOCK_SIZE=$(MASS_BLOCK_SIZE) to MASS_OPTS
MASS_BLOCK_SIZE		= 512 
MASS_OPTS = -DMAX_AGENTS=$(MASS_MAX_AGENTS) -DMAX_NEIGHBORS=$(MASS_MAX_NEIGHBORS) -DMAX_DIMS=$(MASS_MAX_DIMS) -DN_DESTINATIONS=$(MASS_N_DESTINATIONS) -DBLOCK_SIZE=$(MASS_BLOCK_SIZE)

# CUDA Variables
CUDA_ROOT_DIR		= /usr/local/cuda
CUDA_LIB_DIR		= -L$(CUDA_ROOT_DIR)/lib64 -L/usr/local/cuda/samples/common/lib/linux/x86_64
CUDA_INCLUDE_DIR	= -I$(CUDA_ROOT_DIR)/include
NVCC_FLAGS			= -Wno-deprecated-gpu-targets -rdc=true -std=c++17 $(MASS_OPTS)

# SimViz Variables
SIMVIZ_INCLUDE		= -I$(LIB_DIR)/glfw-$(GLFW_VERSION)/include -I$(LIB_DIR)/glad/include -I$(PROJECT_DIR)/simviz/include
SIMVIZ_LIB			= $(LIB_DIR)/simvizlib/simviz.a
GLFW_VERSION		= 3.3.6

# GoogleTest Variables
GOOGLE_TEST_VERSION	= v1.14.0
TEST_LIB_DIR		= -L$(LIB_DIR)/gtest/lib64
TEST_INCLUDE_DIR	= -I$(LIB_DIR)/gtest/include

build::
	echo "Building $(PROJECT_NAME)..."
	mkdir -p $(BUILD_DIR)/$(PROJECT_NAME)
	cd $(BUILD_DIR)/$(PROJECT_NAME) && nvcc $(NVCC_FLAGS) $(CUDA_INCLUDE_DIR) $(SIMVIZ_INCLUDE) $(MASS_INCLUDE) -c $(PROJECT_DIR)/src/*.c*
	nvcc $(NVCC_FLAGS) -lcurand $(CUDA_LIB_DIR) $(SIMVIZ_LIB) $(MASS_LIBS) build/$(PROJECT_NAME)/*.o -o bin/$(PROJECT_NAME)
	echo "$(PROJECT_NAME) build complete."

build-simviz:
	echo "Building SimViz..."
	mkdir -p $(BUILD_DIR)/simviz
	cd $(BUILD_DIR)/simviz && g++ -std=c++11 -c $(SIMVIZ_INCLUDE) $(PROJECT_DIR)/simviz/main.cpp
	cd $(BUILD_DIR)/simviz && g++ main.o $(BUILD_DIR)/glfw/src/libglfw3.a -pthread -ldl -lX11 $(SIMVIZ_INCLUDE) $(LIB_DIR)/glad/src/glad.c -o $(BIN_DIR)/simviz
	rm -rf $(BUILD_DIR)/simviz
	echo "SimViz build complete."

build-simviz-lib: install-simviz-deps
	echo "Building SimViz library..."
	rm -rf $(BUILD_DIR)/simvizlib
	rm -rf $(LIB_DIR)/simvizlib
	mkdir -p $(BUILD_DIR)/simvizlib
	mkdir -p $(LIB_DIR)/simvizlib
	cd $(BUILD_DIR)/simvizlib && g++ -std=c++11 -c $(SIMVIZ_INCLUDE) -c $(PROJECT_DIR)/simviz/include/*.cpp
	ar ru $(LIB_DIR)/simvizlib/simviz.a build/simvizlib/*.o
	ranlib $(LIB_DIR)/simvizlib/simviz.a
	echo "SimViz library build complete."

clean::
	rm -rf build
	rm -rf bin
	rm -rf lib

develop:: install-mass install-google-test build-simviz-lib
	mkdir -p build
	mkdir -p bin
	mkdir -p lib
	echo "$(PROJECT_NAME) Dependencies installed."

install-glad:
	mkdir -p $(LIB_DIR)
	rm -rf $(LIB_DIR)/glad && mkdir -p $(LIB_DIR)/glad
	cd $(LIB_DIR)/glad && unzip $(DEPS_DIR)/glad.zip

install-glfw:
	mkdir -p $(LIB_DIR)
	rm -rf $(LIB_DIR)/glfw-$(GLFW_VERSION) $(LIB_DIR)/glfw-$(GLFW_VERSION).zip $(BUILD_DIR)/glfw
	cd $(LIB_DIR) && wget -O glfw-$(GLFW_VERSION).zip https://github.com/glfw/glfw/releases/download/$(GLFW_VERSION)/glfw-$(GLFW_VERSION).zip
	cd $(LIB_DIR) && unzip glfw-$(GLFW_VERSION).zip
	cd $(LIB_DIR) && rm glfw-$(GLFW_VERSION).zip
	cmake -S $(LIB_DIR)/glfw-$(GLFW_VERSION)/ -B $(BUILD_DIR)/glfw
	cd $(BUILD_DIR)/glfw && make

install-google-test:
	mkdir -p $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/gtest
	mkdir -p $(BUILD_DIR)/gtest
	cd $(BUILD_DIR)/gtest && git clone https://github.com/google/googletest.git -b $(GOOGLE_TEST_VERSION)
	mkdir -p $(BUILD_DIR)/gtest/googletest/build
	cd $(BUILD_DIR)/gtest/googletest/build && cmake -DCMAKE_INSTALL_PREFIX="$(LIB_DIR)/gtest" -DCMAKE_BUILD_TYPE=Release ..
	cd $(BUILD_DIR)/gtest/googletest/build && make && make install
	rm -rf $(BUILD_DIR)/gtest

install-mass:
	echo "Installing MASS"
	mkdir -p $(LIB_DIR)
	rm -rf $(MASS_DIR)
	mkdir -p $(MASS_DIR)
	cd $(MASS_DIR) && git clone $(MASS_GIT_URL) $(MASS_REPO)
	cd $(MASS_REPO) && git checkout $(MASS_VERSION)
	cd $(MASS_REPO) && NVCC_OPTS="$(MASS_OPTS)" make install

install-simviz-deps: install-glfw install-glad
	echo "SimViz dependencies installed."

test::
	echo "Building test..."
	mkdir -p $(BUILD_DIR)/test
	cp $(BUILD_DIR)/$(PROJECT_NAME)/* $(BUILD_DIR)/test/
	rm $(BUILD_DIR)/test/main.o
	cd $(BUILD_DIR)/test && nvcc $(NVCC_FLAGS) $(CUDA_INCLUDE_DIR) $(TEST_INCLUDE_DIR) $(MASS_INCLUDE) $(SIMVIZ_INCLUDE) $(SRC_INCLUDE) -c $(PROJECT_DIR)/test/*.c*
	nvcc $(NVCC_FLAGS) -lcurand -lgtest $(CUDA_LIB_DIR) $(TEST_LIB_DIR) $(MASS_LIBS) $(SIMVIZ_LIB) build/test/*.o -o bin/test
	./bin/test

# To rebuild the MASS library using the specified MASS version
# and rebuild this project as well, run:
rebuild-mass:: install-mass build