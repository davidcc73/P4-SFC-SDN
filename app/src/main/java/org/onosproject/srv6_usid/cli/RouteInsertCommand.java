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
package org.onosproject.srv6_usid.cli;

import org.apache.karaf.shell.api.action.Argument;
import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.Completion;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onlab.packet.IpAddress;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.cli.net.DeviceIdCompleter;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onlab.packet.MacAddress;
import org.onosproject.srv6_usid.Ipv6RoutingComponent;

/**
 * Ipv6 Route Insert Command
 */
@Service
@Command(scope = "onos", name = "route-insert",
         description = "Insert a rule in a KShort or ECMP routing tables")
public class RouteInsertCommand extends AbstractShellCommand {

    @Argument(index = 0, name = "uri", description = "Device ID",
              required = true, multiValued = false)
    @Completion(DeviceIdCompleter.class)
    String uri = null;

    @Argument(index = 1, name = "table",
            description = "to each table the command is for",
            required = true, multiValued = false)
    String table = null;

    @Argument(index = 2, name = "ipv6NetAddress",
            description = "IPv6 address",
            required = true, multiValued = false)
    String ipv6NetAddr = null;

    @Argument(index = 3, name = "dst_mask",
            description = "IPv6 dst_mask",
            required = false, multiValued = false)
    int dst_mask = 64;

    @Argument(index = 4, name = "macDstAddr",
            description = "MAC destination address",
            required = true, multiValued = false)
    String macDstAddr = null;

    @Override
    protected void doExecute() {
        int max_FlowLabel = 3;
        DeviceService deviceService = get(DeviceService.class);
        Ipv6RoutingComponent app = get(Ipv6RoutingComponent.class);

        Device device = deviceService.getDevice(DeviceId.deviceId(uri));
        if (device == null) {
            print("Device \"%s\" is not found", uri);
            return;
        }
        
        IpAddress destIp = IpAddress.valueOf(ipv6NetAddr);
        MacAddress nextHop = MacAddress.valueOf(macDstAddr);

        print("Installing route on device %s", uri);
        /*
        if(table.equals("KShort")){
            app.insertRoutingRuleKShort(device.id(), destIp, dst_mask, nextHop);
        }else if(table.equals("ECMP")){
            for(int currentFlowLabel = 0; currentFlowLabel <= max_FlowLabel; currentFlowLabel++){ 
                //mask 0, to forward host traffic to them, no matter the source of it
                app.insertRoutingRuleECMP(device.id(), Ip6Address.valueOf("0:0:0::0"), destIp, 0, dst_mask, currentFlowLabel, nextHop);
            }
        }
        else{
            print("Invalid table");
        }  
        */
    }

}
