#include <chrono>
#include <cmath>
#include <memory>

#include "lab2/point_cloud_adapter.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace lab2
{
using namespace std::chrono_literals;

class CloudPublisher : public rclcpp::Node
{
private:
  rclcpp::Publisher<AdaptedPointCloud>::SharedPtr pub;
  rclcpp::TimerBase::SharedPtr timer;
  std::size_t count = 0;

public:
  explicit CloudPublisher(const rclcpp::NodeOptions& options)
  : Node("cloud_publisher", options)
  {
    pub = create_publisher<AdaptedPointCloud>("cloud", 10);

    timer = create_wall_timer(1s, [this]() { publish_cloud(); });
  }

private:
  void publish_cloud()
  {
    constexpr std::size_t points = 1000;
    const float phase = static_cast<float>(count) * 0.1f;

    auto cloud = std::make_unique<PointCloudXYZ>();
    cloud->header.frame_id = "map";
    cloud->header.stamp = static_cast<uint64_t>(now().nanoseconds() / 1'000);  // PCL uses microseconds
    cloud->reserve(points);

    for (std::size_t i = 0; i < points; ++i) {
      const float t = static_cast<float>(i) * 0.05f;
      cloud->push_back({std::cos(t + phase), std::sin(t + phase), t * 0.1f});
    }

    RCLCPP_INFO(
      get_logger(), "Publishing cloud #%zu: %zu points at %p (conversions so far: to_ros=%zu, to_pcl=%zu)",
      ++count, cloud->size(), static_cast<void*>(cloud.get()),
      to_ros_conversions.load(), to_pcl_conversions.load());

    // Handing over the unique_ptr lets intra-process delivery move the object
    // to a subscriber instead of copying or converting it.
    pub->publish(std::move(cloud));
  }
};

}  // namespace lab2

RCLCPP_COMPONENTS_REGISTER_NODE(lab2::CloudPublisher)
