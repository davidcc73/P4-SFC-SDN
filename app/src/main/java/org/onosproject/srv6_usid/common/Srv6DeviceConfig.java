/*
 * Copyright 2019-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.onosproject.srv6_usid.common;

import org.onlab.packet.IpAddress;
import org.onlab.packet.MacAddress;
import org.onosproject.net.DeviceId;
import org.onosproject.net.config.Config;

/**
 * Device configuration object for the SRv6 srv6_usid application.
 */
public class Srv6DeviceConfig extends Config<DeviceId> {

    public static final String CONFIG_KEY = "srv6DeviceConfig";
    private static final String MY_STATION_MAC = "myStationMac";
    private static final String SUB_NET_IP = "subNetIP";

    /**
     * Gets the MAC address of the switch.
     *
     * @return MAC address of the switch. Or null if not configured.
     */
    public MacAddress myStationMac() {
        String mac = get(MY_STATION_MAC, null);
        return mac != null ? MacAddress.valueOf(mac) : null;
    }

    /**
     * Gets the subNetIP instruction of the switch.
     *
     * @return subNetIP instruction of the router. Or null if not configured.
     */
    public IpAddress mySubNetIP() {
        String subNetIP = get(SUB_NET_IP, null);
        return subNetIP != null ? IpAddress.valueOf(subNetIP) : null;
    }
}
