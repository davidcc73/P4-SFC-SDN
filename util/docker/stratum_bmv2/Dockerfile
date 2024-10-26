# Copyright 2018-present Open Networking Foundation
# SPDX-License-Identifier: Apache-2.0

# This Dockerfile expects the stratum root as its scope, hence you should build
# from root e.g.:
# docker build -t <some tag> -f tools/mininet/Dockerfile .

# We use a 2-stage build. Build all tools first, then copy only the strict necessary
# to a new image with runtime dependencies.

FROM stratumproject/build:build as builder
ENV BUILD_DEPS \
    python3-setuptools \
    python3-pip \
    help2man \
    git

RUN apt-get update && \
    apt-get install -y --no-install-recommends ${BUILD_DEPS}


# Build Mininet
RUN mkdir /tmp/mininet
WORKDIR /tmp/mininet
RUN curl -L https://github.com/mininet/mininet/tarball/master | \
    tar xz --strip-components 1

# Install in a special directory that we will copy to the runtime image.
RUN mkdir -p /output/usr/local/lib
RUN PREFIX=/output make install-mnexec install-manpages
RUN python3 setup.py install --root /output --prefix /usr/local

# Install `m` utility so user can attach to a mininet host directly
RUN cp util/m /output/bin/m && sed -i 's#sudo##g' /output/bin/m

# Install `host-cmd` utility so user can run commands on a host directly
COPY ./tools/mininet/host-cmd.sh /output/bin/host-cmd
RUN chmod +x /output/bin/host-cmd

ENV PIP_DEPS \
    git+https://github.com/p4lang/ptf.git \
    googleapis-common-protos==1.6.0 \
    ipaddress

RUN pip3 install --no-cache-dir --root /output $PIP_DEPS

# As well as the P4Runtime Python bindings installed by PI. This is not needed
# to run mininet, but it's useful to execute Python scripts acting as a
# P4Runtime client, e.g. control plane apps or PTF tests.
RUN pip3 install --root /output p4runtime==1.3.0








# Final stage, runtime.
FROM bitnami/minideb:buster as runtime

LABEL maintainer="Stratum dev <stratum-dev@lists.stratumproject.org>"
LABEL description="This is a modified version of, Docker-based Mininet image that uses stratum_bmv2 as the default switch, the only differences are the addition of X11 forwarding, scapy and pip3 at runtime (to install scapy), the alterations were done by modifying the original stratum-main/tools/mininet/Dockerfile, the newer version can be seen at https://github.com/davidcc73/p4-srv6-INT util/docker/stratum_bmv2/Dockerfile"


# X11 forwarding
# Install necessary X11 packages
RUN install_packages \
    xserver-xorg-core \
    xserver-xorg-video-vmware \ 
    xserver-xorg-input-evdev \
    x11-xserver-utils \
    x11-xkb-utils \
    x11-utils \
    xinit \
    xterm \
    x11-apps \
    openbox

# Create minimal ~/.xinitrc
RUN echo "#!/bin/sh" > ~/.xinitrc && \
    echo "xterm &" >> ~/.xinitrc && \
    echo "exec openbox" >> ~/.xinitrc && \
    chmod +x ~/.xinitrc

RUN apt-get update && \
    apt-get install -y --no-install-recommends ${X11_DEPS}


#Enable X11 forwarding
ENV DISPLAY=:0

# Mininet and BMv2 simple_switch runtime dependencies
ENV RUNTIME_DEPS \
    iproute2 \
    iputils-ping \
    net-tools \
    ethtool \
    socat \
    psmisc \
    procps \
    iperf \
    arping \
    telnet \
    python3 \
    python3-pexpect \
    tcpdump \
    screen \
    make
RUN install_packages $RUNTIME_DEPS

# Final stage, runtime.
ENV RUNTIME_DEPS2 \
    python3-setuptools \
    python3-pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends ${RUNTIME_DEPS2}
# Install scapy
RUN pip3 install scapy


COPY --from=builder /output /
ADD ./stratum-bmv2_0.0.1_amd64.deb /
RUN install_packages /stratum-bmv2_0.0.1_amd64.deb
RUN ldconfig

WORKDIR /root
COPY stratum/hal/bin/bmv2/dummy.json ./dummy.json
COPY tools/mininet/stratum.py ./stratum.py
ENV PYTHONPATH /root:/usr/local/lib/python3.7/dist-packages:/usr/local/lib/python3.7/site-packages

# We need to expose one port per stratum_bmv2 instance, hence the number of
# exposed ports limit the number of switches that can be controlled from an
# external P4Runtime controller.

#EXPOSE 50001-50100
#ENTRYPOINT ["mn", "--custom", "/root/stratum.py", "--switch", "stratum-bmv2", "--host", "no-offload-host", "--controller", "none"]

ENV DOCKER_RUN true

ENTRYPOINT []