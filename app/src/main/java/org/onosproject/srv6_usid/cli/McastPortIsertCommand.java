package org.onosproject.srv6_usid.cli;


import java.util.Arrays;

import org.apache.karaf.shell.api.action.Argument;
import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.Completion;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.cli.net.DeviceIdCompleter;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.srv6_usid.L2BridgingComponent;


@Service
@Command(scope = "onos", name = "mcast_port_add",
        description = "In a given device create a multicast group with the given ports, so packets associated to that group will be forwarded to those ports. IF GROUP ALREADY EXISTS, NO CHANGES CAN BE MADE TO IT, NO ERROR MSG WILL BE RETURNED FOR THIS CASE")
public class McastPortIsertCommand extends AbstractShellCommand {

    @Argument(index = 0, name = "uri", description = "Device ID",
            required = true, multiValued = false)
    @Completion(DeviceIdCompleter.class)
    String uri = null;

    @Argument(index = 1, name = "Multicast Group",
            description = "Multicast Group to which the ports are added",
            required = true, multiValued = false)
    int mcast_group;

    @Argument(index = 2, name = "Ports",
            description = "One or more ports to be added to the Multicast Group, on the given device",
            required = true, multiValued = false)
    String ports_string = null;


    @Override
    protected void doExecute() {
        DeviceService deviceService = get(DeviceService.class);
        L2BridgingComponent app = get(L2BridgingComponent.class);

        // Retrieve device by URI
        Device device = deviceService.getDevice(DeviceId.deviceId(uri));
        if (device == null) {
            print("Device \"%s\" is not found", uri);
            return;
        }

        int[] ports = Arrays.stream(ports_string.split(" "))
                          .mapToInt(Integer::parseInt)
                          .toArray();

        print("Installing rule on device %s", uri);
        String res = app.addMcastGroupAndPorts(device.id(), mcast_group, ports);

        if(res != null){
            print("A problem occured\n");
            print(res);
        } 

    }
}