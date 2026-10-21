cmake_minimum_required(VERSION 3.8)
project(simple_arm_moveit_config)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/move_arm.py DESTINATION lib/${PROJECT_NAME})

ament_package()
