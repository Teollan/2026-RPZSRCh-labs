#pragma once

#include <atomic>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>

#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

#include "rclcpp/logging.hpp"
#include "rclcpp/type_adapter.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "sensor_msgs/msg/point_field.hpp"

namespace lab2
{

using PointCloudXYZ = pcl::PointCloud<pcl::PointXYZ>;

inline std::atomic<std::size_t> to_ros_conversions{0};
inline std::atomic<std::size_t> to_pcl_conversions{0};

}  // namespace lab2

template<>
struct rclcpp::TypeAdapter<lab2::PointCloudXYZ, sensor_msgs::msg::PointCloud2>
{
  using is_specialized = std::true_type;
  using custom_type = lab2::PointCloudXYZ;
  using ros_message_type = sensor_msgs::msg::PointCloud2;

  // PCL -> ROS: pack x, y, z of every point as three float32 (12 bytes per point).
  static void convert_to_ros_message(const custom_type& source, ros_message_type& destination)
  {
    const auto count = ++lab2::to_ros_conversions;
    RCLCPP_INFO(
      rclcpp::get_logger("point_cloud_adapter"),
      "PCL -> PointCloud2 conversion #%zu (%zu points)", count, source.size());

    // PCL stamps are microseconds; ROS uses seconds + nanoseconds.
    destination.header.frame_id = source.header.frame_id;
    destination.header.stamp.sec = static_cast<int32_t>(source.header.stamp / 1'000'000);
    destination.header.stamp.nanosec = static_cast<uint32_t>((source.header.stamp % 1'000'000) * 1'000);

    // Trust width x height only if it matches the number of points; otherwise
    // describe the cloud as unordered (one row).
    const bool organized = static_cast<std::size_t>(source.width) * source.height == source.size();
    destination.width = organized ? source.width : static_cast<uint32_t>(source.size());
    destination.height = organized ? source.height : 1;

    destination.fields.resize(3);
    const char* names[] = {"x", "y", "z"};
    for (uint32_t i = 0; i < 3; ++i) {
      destination.fields[i].name = names[i];
      destination.fields[i].offset = i * sizeof(float);
      destination.fields[i].datatype = sensor_msgs::msg::PointField::FLOAT32;
      destination.fields[i].count = 1;
    }

    destination.is_bigendian = (std::endian::native == std::endian::big);
    destination.point_step = 3 * sizeof(float);
    destination.row_step = destination.point_step * destination.width;
    destination.is_dense = source.is_dense;

    destination.data.resize(static_cast<std::size_t>(destination.row_step) * destination.height);
    auto* out = destination.data.data();
    for (const auto& p : source.points) {
      const float xyz[3] = {p.x, p.y, p.z};
      std::memcpy(out, xyz, sizeof(xyz));
      out += destination.point_step;
    }
  }

  // ROS -> PCL: find the x, y, z fields and read them from every point.
  static void convert_to_custom(const ros_message_type & source, custom_type & destination)
  {
    const auto count = ++lab2::to_pcl_conversions;
    RCLCPP_INFO(
      rclcpp::get_logger("point_cloud_adapter"),
      "PointCloud2 -> PCL conversion #%zu (%u points)", count, source.width * source.height);

    if (source.is_bigendian != (std::endian::native == std::endian::big)) {
      throw std::runtime_error("PointCloud2 byte order differs from this machine's");
    }

    // Offsets of x, y, z inside one point. Other fields (intensity, rgb...) are ignored.
    uint32_t offsets[3];
    const char* names[] = {"x", "y", "z"};
    for (int i = 0; i < 3; ++i) {
      bool found = false;

      for (const auto& field : source.fields) {
        if (field.name == names[i]) {
          if (field.datatype != sensor_msgs::msg::PointField::FLOAT32) {
            throw std::runtime_error(std::string("PointCloud2 field '") + names[i] + "' is not float32");
          }

          offsets[i] = field.offset;
          found = true;

          break;
        }
      }

      if (!found) {
        throw std::runtime_error(std::string("PointCloud2 has no '") + names[i] + "' field");
      }
    }

    const std::size_t needed = static_cast<std::size_t>(source.row_step) * source.height;
    if (source.data.size() < needed) {
      throw std::runtime_error("PointCloud2 data is shorter than row_step * height");
    }

    destination.header.frame_id = source.header.frame_id;
    destination.header.stamp =
      static_cast<uint64_t>(source.header.stamp.sec) * 1'000'000 + source.header.stamp.nanosec / 1'000;
    destination.width = source.width;
    destination.height = source.height;
    destination.is_dense = source.is_dense;
    destination.points.resize(static_cast<std::size_t>(source.width) * source.height);

    std::size_t i = 0;
    for (uint32_t row = 0; row < source.height; ++row) {
      const uint8_t* point = source.data.data() + static_cast<std::size_t>(row) * source.row_step;

      for (uint32_t col = 0; col < source.width; ++col, point += source.point_step) {
        auto& p = destination.points[i++];
        std::memcpy(&p.x, point + offsets[0], sizeof(float));
        std::memcpy(&p.y, point + offsets[1], sizeof(float));
        std::memcpy(&p.z, point + offsets[2], sizeof(float));
      }
    }
  }
};

namespace lab2
{

using AdaptedPointCloud = rclcpp::TypeAdapter<PointCloudXYZ, sensor_msgs::msg::PointCloud2>;

}  // namespace lab2
