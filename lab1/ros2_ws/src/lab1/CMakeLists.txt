cmake_minimum_required(VERSION 3.20)
project(lab1)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

add_executable(lab1 src/lab1.cpp)
target_compile_features(lab1 PUBLIC c_std_17 cxx_std_20)
target_link_libraries(lab1 ${rclcpp_TARGETS})

install(TARGETS lab1
  DESTINATION lib/${PROJECT_NAME})

foreach(comp A B C)
  add_library(${comp} SHARED src/${comp}.component.cpp)
  target_compile_features(${comp} PUBLIC c_std_17 cxx_std_20)
  target_link_libraries(${comp}
    ${rclcpp_TARGETS}
    ${rclcpp_components_TARGETS}
    ${rclcpp_lifecycle_TARGETS}
  )
  rclcpp_components_register_nodes(${comp} "lab1::${comp}")
endforeach()

install(TARGETS A B C
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
