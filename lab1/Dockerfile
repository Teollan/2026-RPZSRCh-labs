FROM ros:lyrical

RUN echo 'source /opt/ros/$ROS_DISTRO/setup.bash' >> /root/.bashrc

WORKDIR /ros2_ws

COPY --chmod=755 entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["bash"]
