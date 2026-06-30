cmake_minimum_required(VERSION 3.16)
project(li7_benchmark LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Geant4 REQUIRED)
include(${Geant4_USE_FILE})

add_executable(li7_benchmark src/main.cc)
target_link_libraries(li7_benchmark ${Geant4_LIBRARIES})

