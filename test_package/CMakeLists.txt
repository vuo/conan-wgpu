cmake_minimum_required(VERSION 3.0.0)
project(PackageTest C)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(KEEP_RPATHS)

add_executable(test_package test_package.c)
target_link_libraries(test_package PRIVATE ${CONAN_LIBS})
