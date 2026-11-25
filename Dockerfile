FROM ros:lyrical

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        libpcl-dev \
    && rm -rf /var/lib/apt/lists/*

# Run as the image's `ubuntu` user (UID/GID 1000, same as the host user), so
# files created in the mounted repo stay owned by the host user, not root.
# Passwordless sudo keeps `sudo apt install ...` available inside.
RUN echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ubuntu \
    && chmod 0440 /etc/sudoers.d/ubuntu

# System-wide, so it applies to whichever user opens a shell.
RUN echo 'source /opt/ros/$ROS_DISTRO/setup.bash' >> /etc/bash.bashrc

WORKDIR /RPZSRCh

COPY --chmod=755 entrypoint.sh /entrypoint.sh

USER ubuntu

ENTRYPOINT ["/entrypoint.sh"]

CMD ["bash"]
