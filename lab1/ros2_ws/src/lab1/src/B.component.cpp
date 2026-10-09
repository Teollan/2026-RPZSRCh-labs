#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace lab1
{

class B : public rclcpp_lifecycle::LifecycleNode
{
public:
  using CallbackReturn =
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

  explicit B(const rclcpp::NodeOptions& options)
  : LifecycleNode("b", options)
  {
    RCLCPP_INFO(get_logger(), "B constructed, state: %s",
      get_current_state().label().c_str());
  }

  CallbackReturn on_configure(const rclcpp_lifecycle::State& previous) override
  {
    RCLCPP_INFO(get_logger(), "on_configure: %s -> inactive", previous.label().c_str());
    return CallbackReturn::SUCCESS;
  }

  CallbackReturn on_activate(const rclcpp_lifecycle::State& previous) override
  {
    RCLCPP_INFO(get_logger(), "on_activate: %s -> active", previous.label().c_str());
    return LifecycleNode::on_activate(previous);
  }

  CallbackReturn on_deactivate(const rclcpp_lifecycle::State& previous) override
  {
    RCLCPP_INFO(get_logger(), "on_deactivate: %s -> inactive", previous.label().c_str());
    return LifecycleNode::on_deactivate(previous);
  }

  CallbackReturn on_cleanup(const rclcpp_lifecycle::State& previous) override
  {
    RCLCPP_INFO(get_logger(), "on_cleanup: %s -> unconfigured", previous.label().c_str());
    return CallbackReturn::SUCCESS;
  }

  CallbackReturn on_shutdown(const rclcpp_lifecycle::State& previous) override
  {
    RCLCPP_INFO(get_logger(), "on_shutdown: %s -> finalized", previous.label().c_str());
    return CallbackReturn::SUCCESS;
  }
};

}  // namespace lab1

RCLCPP_COMPONENTS_REGISTER_NODE(lab1::B)
