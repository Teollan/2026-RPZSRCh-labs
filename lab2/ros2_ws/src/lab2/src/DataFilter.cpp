#include <algorithm>
#include <cctype>
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"
#include "std_msgs/msg/string.hpp"
#include "std_srvs/srv/trigger.hpp"

namespace lab2
{

  class DataFilter : public rclcpp::Node
  {
  private:
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr lowercase_sub;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr uppercase_pub;
    rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr reset_srv;

  public:
    explicit DataFilter(const rclcpp::NodeOptions &options) : Node("data_filter", options)
    {
      create_reset_service();
      create_uppercase_publisher();
    }

  private:
    void create_reset_service() {
      reset_srv = create_service<std_srvs::srv::Trigger>(
        "reset_filter",
        [this](
          const std::shared_ptr<std_srvs::srv::Trigger::Request> _,
          const std::shared_ptr<std_srvs::srv::Trigger::Response> res
        ) {
          RCLCPP_INFO(this->get_logger(), "reset_filter called");

          res->success = true;
          res->message = "OK";
        }
      );

      reset_srv->configure_introspection(
        get_clock(),
        rclcpp::SystemDefaultsQoS(),
        RCL_SERVICE_INTROSPECTION_CONTENTS
      );
    }

    void create_uppercase_publisher() {
      rclcpp::PublisherOptions pub_options;

      pub_options.event_callbacks.matched_callback =
      [this](rclcpp::MatchedInfo& s) {
        if (lowercase_sub) {
          if (s.current_count == 0) {
            RCLCPP_INFO(this->get_logger(), "Last subscription is disconnected.");

            unsubscribe_from_lowercase_topic();
          }
        } else {
          if (s.current_count != 0) {
            RCLCPP_INFO(this->get_logger(), "First subscription is connected.");

            subscribe_to_lowercase_topic();
          }
        }
      };

      pub_options.qos_overriding_options = rclcpp::QosOverridingOptions{
        rclcpp::QosPolicyKind::Depth,
        rclcpp::QosPolicyKind::Reliability,
        rclcpp::QosPolicyKind::Durability,
      };

      uppercase_pub = this->create_publisher<std_msgs::msg::String>("uppercase_topic", rclcpp::QoS(1).transient_local(), pub_options);
    }

    void subscribe_to_lowercase_topic() {
      lowercase_sub = this->create_subscription<std_msgs::msg::String>(
        "lowercase_topic",
        10,
        [this](const std_msgs::msg::String& input) {
          RCLCPP_INFO(this->get_logger(), "I heard: '%s'", input.data.c_str());

          auto output = std_msgs::msg::String();
          output.data = std::string(input.data.size(), '\0');

          std::transform(
            input.data.begin(),
            input.data.end(),
            output.data.begin(),
            [](unsigned char c){ return std::toupper(c); }
          );

          RCLCPP_INFO(this->get_logger(), "I sent: '%s'", output.data.c_str());

          uppercase_pub->publish(output);
        }
      );
    }
  
    void unsubscribe_from_lowercase_topic() {
      lowercase_sub = nullptr;
    }
  };

} // namespace lab2

RCLCPP_COMPONENTS_REGISTER_NODE(lab2::DataFilter)
