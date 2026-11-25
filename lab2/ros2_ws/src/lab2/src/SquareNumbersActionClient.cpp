#include <chrono>
#include <memory>
#include <sstream>

#include "lab2_interfaces/action/square_numbers.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace lab2
{
using namespace std::chrono_literals;

class SquareNumbersActionClient : public rclcpp::Node
{
public:
  using Action = lab2_interfaces::action::SquareNumbers;
  using GoalHandle = rclcpp_action::ClientGoalHandle<Action>;

private:
  rclcpp_action::Client<Action>::SharedPtr client;
  rclcpp::TimerBase::SharedPtr timer;

public:
  explicit SquareNumbersActionClient(const rclcpp::NodeOptions& node_options = rclcpp::NodeOptions())
    : Node("square_numbers_action_client", node_options)
  {
    this->client = rclcpp_action::create_client<Action>(
      this->get_node_base_interface(),
      this->get_node_graph_interface(),
      this->get_node_logging_interface(),
      this->get_node_waitables_interface(),
      "square_numbers"
    );

    this->timer = this->create_wall_timer(
      500ms,
      [this]() { return this->send_goal(); }
    );
  }

  void send_goal()
  {

    this->timer->cancel();

    if (!this->client->wait_for_action_server(10s)) {
      RCLCPP_ERROR(this->get_logger(), "Action server not available after waiting");

      rclcpp::shutdown();
      return;
    }

    auto goal_msg = Action::Goal();
    goal_msg.numbers = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };

    RCLCPP_INFO(this->get_logger(), "Sending goal");

    auto send_goal_options = rclcpp_action::Client<Action>::SendGoalOptions();
    send_goal_options.goal_response_callback = [this] (
      const GoalHandle::SharedPtr& goal_handle)
      {
        if (!goal_handle) {
          RCLCPP_ERROR(this->get_logger(), "GoalHandle was rejected by server");
        } else {
          RCLCPP_INFO(this->get_logger(), "GoalHandle accepted by server, waiting for result");
        }
      };

    send_goal_options.feedback_callback = [this](
      GoalHandle::SharedPtr,
      const std::shared_ptr<const Action::Feedback> feedback)
      {
        RCLCPP_INFO(
          this->get_logger(),
          "Square with index [%d] received: %f",
          feedback->index,
          feedback->square
        );
      };

    send_goal_options.result_callback = [this](
      const GoalHandle::WrappedResult& result)
      {
        switch (result.code) {
          case rclcpp_action::ResultCode::SUCCEEDED:
            break;
          case rclcpp_action::ResultCode::ABORTED:
            RCLCPP_ERROR(this->get_logger(), "GoalHandle was aborted");
            return;
          case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_ERROR(this->get_logger(), "GoalHandle was canceled");
            return;
          default:
            RCLCPP_ERROR(this->get_logger(), "Unknown result code");
            return;
        }

        std::stringstream ss;
        ss << "Result received: ";
        for (auto number : result.result->squares) {
          ss << number << " ";
        }

        RCLCPP_INFO(this->get_logger(), "%s", ss.str().c_str());
        rclcpp::shutdown();
      };

    this->client->async_send_goal(goal_msg, send_goal_options);
  }
};  // class SquareNumbersActionClient

}  // namespace lab2

RCLCPP_COMPONENTS_REGISTER_NODE(lab2::SquareNumbersActionClient)