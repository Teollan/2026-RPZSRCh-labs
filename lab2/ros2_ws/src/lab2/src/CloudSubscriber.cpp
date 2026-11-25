#include <memory>

#include "lab2/point_cloud_adapter.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace lab2
{

class CloudSubscriber : public rclcpp::Node
{
private:
  rclcpp::Subscription<AdaptedPointCloud>::SharedPtr sub;

public:
  explicit CloudSubscriber(const rclcpp::NodeOptions& options)
  : Node("cloud_subscriber", options)
  {
    sub = create_subscription<AdaptedPointCloud>(
      "cloud",
      10,
      [this](std::unique_ptr<PointCloudXYZ> cloud) {
        const auto& first = cloud->front();

        RCLCPP_INFO(
          get_logger(), "Received cloud: %zu points at %p, first (%.2f, %.2f, %.2f) "
          "(conversions so far: to_ros=%zu, to_pcl=%zu)",
          cloud->size(), static_cast<void*>(cloud.get()), first.x, first.y, first.z,
          to_ros_conversions.load(), to_pcl_conversions.load());
      }
    );
  }
};

}  // namespace lab2

RCLCPP_COMPONENTS_REGISTER_NODE(lab2::CloudSubscriber)
