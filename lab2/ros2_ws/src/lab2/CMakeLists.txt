cmake_minimum_required(VERSION 3.20)
project(lab2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(lab2_interfaces REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(PCL REQUIRED COMPONENTS common)

foreach(comp DataFilter SquareNumbersActionServer SquareNumbersActionClient CloudPublisher CloudSubscriber)
  add_library(${comp} SHARED src/${comp}.cpp)
  target_compile_features(${comp} PUBLIC c_std_17 cxx_std_20)
  target_include_directories(${comp} PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  )
  target_include_directories(${comp} SYSTEM PUBLIC ${PCL_INCLUDE_DIRS})
  target_link_libraries(${comp}
    ${rclcpp_TARGETS}
    ${rclcpp_components_TARGETS}
    ${std_msgs_TARGETS}
    ${std_srvs_TARGETS}
    ${rclcpp_action_TARGETS}
    ${lab2_interfaces_TARGETS}
    ${sensor_msgs_TARGETS}
    ${PCL_LIBRARIES}
  )
endforeach()

rclcpp_components_register_nodes(DataFilter "lab2::DataFilter")
rclcpp_components_register_nodes(SquareNumbersActionServer "lab2::SquareNumbersActionServer")
rclcpp_components_register_nodes(CloudPublisher "lab2::CloudPublisher")
rclcpp_components_register_nodes(CloudSubscriber "lab2::CloudSubscriber")

rclcpp_components_register_node(SquareNumbersActionClient
  PLUGIN "lab2::SquareNumbersActionClient"
  EXECUTABLE square_numbers_client)

install(TARGETS DataFilter SquareNumbersActionServer SquareNumbersActionClient CloudPublisher CloudSubscriber
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

add_executable(reset_client src/ResetFilterClient.cpp)
target_compile_features(reset_client PUBLIC c_std_17 cxx_std_20)
target_link_libraries(reset_client
  ${rclcpp_TARGETS}
  ${std_srvs_TARGETS}
)

install(TARGETS reset_client
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
