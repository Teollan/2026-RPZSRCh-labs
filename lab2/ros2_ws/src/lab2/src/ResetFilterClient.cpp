#include <chrono>
#include <cstdio>
#include <future>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "std_srvs/srv/trigger.hpp"

using namespace std::chrono_literals;

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);

    auto node = std::make_shared<rclcpp::Node>("reset_client");
    auto client = node->create_client<std_srvs::srv::Trigger>("reset_filter");

    rclcpp::executors::SingleThreadedExecutor exec;
    exec.add_node(node);

    std::thread worker([&] {
        try {
            if (client->wait_for_service(2s)) {
                auto future = client->async_send_request(std::make_shared<std_srvs::srv::Trigger::Request>());
                
                if (future.wait_for(3s) == std::future_status::ready) {
                    auto res = future.get();

                    printf(
                        "Result: { success: %s, message: %s }\n",
                        res->success ? "true" : "false",
                        res->message.c_str()
                    );
                } else {
                    client->remove_pending_request(future);
                    
                    printf("Result: timeout\n");
                }
            } else {
                printf("Service not available!\n");
            }
        } catch (const std::exception& e) {
            fprintf(stderr, "Error: %s\n", e.what());
        }

        rclcpp::shutdown();
    });

    exec.spin();
    worker.join();

    return 0;
}
