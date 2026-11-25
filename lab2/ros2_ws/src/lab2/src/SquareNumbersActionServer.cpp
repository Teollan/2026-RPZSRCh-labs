#include <memory>
#include <sstream>
#include <thread>
#include <vector>

#include "lab2_interfaces/action/square_numbers.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace lab2
{
class SquareNumbersActionServer : public rclcpp::Node
{
public:
  using Action = lab2_interfaces::action::SquareNumbers;
  using GoalHandle = rclcpp_action::ServerGoalHandle<Action>;

private:
  rclcpp_action::Server<Action>::SharedPtr server;

public:
  explicit SquareNumbersActionServer(const rclcpp::NodeOptions& options = rclcpp::NodeOptions())
  : Node("square_numbers_action_server", options)
  {

    auto handle_goal = [this] (
      const rclcpp_action::GoalUUID& uuid,
      std::shared_ptr<const Action::Goal> goal
    ) {
        (void)uuid;

        std::stringstream ss;

        ss << "Received goal request with numbers: ";
        for (auto number : goal->numbers) {
          ss << number << " ";
        }

        RCLCPP_INFO(this->get_logger(), "%s", ss.str().c_str());

        // Reject long goals, to make API more anoying
        if (goal->numbers.size() > 10) {
            return rclcpp_action::GoalResponse::REJECT;
        }

        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
    };

    auto handle_cancel = [this] (
      const std::shared_ptr<GoalHandle> goal_handle
    ) {
        (void)goal_handle;

        RCLCPP_INFO(this->get_logger(), "Received request to cancel goal");

        return rclcpp_action::CancelResponse::ACCEPT;
    };

    auto handle_accepted = [this] (
      const std::shared_ptr<GoalHandle> goal_handle
    ) {
        auto execute_in_thread = [this, goal_handle]() { return this->execute(goal_handle); };

        std::thread{execute_in_thread}.detach();
    };

    this->server = rclcpp_action::create_server<Action>(
      this,
      "square_numbers",
      handle_goal,
      handle_cancel,
      handle_accepted
    );
  }

private: 
  void execute(const std::shared_ptr<GoalHandle> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Executing goal");

    rclcpp::Rate loop_rate(1);

    const auto goal = goal_handle->get_goal();
    const auto& numbers = goal->numbers;

    auto feedback = std::make_shared<Action::Feedback>();

    std::vector<double> squares;

    auto result = std::make_shared<Action::Result>();

    for (int i = 0; (i < numbers.size()) && rclcpp::ok(); ++i) {
      if (goal_handle->is_canceling()) {
        result->squares = squares;
        goal_handle->canceled(result);

        RCLCPP_INFO(this->get_logger(), "GoalHandle canceled");
        return;
      }

      auto square = numbers[i] * numbers[i];
      squares.push_back(square);

      feedback->index = i;
      feedback->square = square;
      goal_handle->publish_feedback(feedback);
      RCLCPP_INFO(this->get_logger(), "Publish feedback");

      loop_rate.sleep();
    }

    if (rclcpp::ok()) {
      result->squares = squares;
      goal_handle->succeed(result);

      RCLCPP_INFO(this->get_logger(), "GoalHandle succeeded");
    }
  }
};  // class SquareNumbersActionServer

}  // namespace lab2

RCLCPP_COMPONENTS_REGISTER_NODE(lab2::SquareNumbersActionServer)