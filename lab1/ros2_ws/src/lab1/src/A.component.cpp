#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace lab1
{

class A : public rclcpp::Node
{
public:
  explicit A(const rclcpp::NodeOptions& options)
  : Node("a", options)
  {
    RCLCPP_INFO(get_logger(), "A constructed");
  }
};

}  // namespace lab1

RCLCPP_COMPONENTS_REGISTER_NODE(lab1::A)
