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
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.cli.net.DeviceIdCompleter;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.srv6_usid.Ipv4RoutingComponent;

@Service
@Command(scope = "onos", name = "table_add",
        description = "Insert a table rule [table_add device table action criteria fields key_fields keys args_fields args]")
public class RouteInsertCommand extends AbstractShellCommand {

    @Argument(index = 0, name = "uri", description = "Device ID",
            required = true, multiValued = false)
    @Completion(DeviceIdCompleter.class)
    String uri = null;

    @Argument(index = 1, name = "table",
            description = "Table to which the command applies",
            required = true, multiValued = false)
    String table = null;

    @Argument(index = 2, name = "action",
            description = "Action triggered",
            required = true, multiValued = false)
    String action = null;

    @Argument(index = 3, name = "criteria",
            description = "Conparison criteria",
            required = true, multiValued = false)
    String criteria = null;

    @Argument(index = 4, name = "fields_key",
        description = "Fields of the keys to match",
        required = true, multiValued = false)
    String fields_key = null;

    @Argument(index = 5, name = "keys",
        description = "Keys to match",
        required = true, multiValued = false)
    String key = null;

    @Argument(index = 6, name = "args_field",
        description = "Fields pf the args for the action",
        required = true, multiValued = false)
    String args_field = null;

    @Argument(index = 7, name = "args",
        description = "args for the action",
        required = true, multiValued = false)
    String arg = null;


    @Override
    protected void doExecute() {
        DeviceService deviceService = get(DeviceService.class);
        Ipv4RoutingComponent app = get(Ipv4RoutingComponent.class);

        // Retrieve device by URI
        Device device = deviceService.getDevice(DeviceId.deviceId(uri));
        if (device == null) {
            print("Device \"%s\" is not found", uri);
            return;
        }

        /*
        print("Device ID (URI): %s", uri);
        print("Table: %s", table);
        print("Action: %s", action);

        print("Criteria: %s", criteria);
        print("Fields of the keys to match: %s", fields_key);
        print("Keys to match: %s", key);
        print("Fields of the args for the action: %s", args_field);
        print("Args for the action: %s", arg)*/


        // parse keys by space
        String[] fields_keys = null;
        String[] keys = null;
        String[] args_fields = null;
        String[] args = null;

        if(!fields_key.trim().equals("")) fields_keys = fields_key.split(" ");
        if(!key.trim().equals("")) keys = key.split(" ");
        if(!args_field.trim().equals("")) args_fields = args_field.split(" ");
        if(!arg.trim().equals("")) args = arg.split(" ");

        // Execute command - replace this line with actual logic to interact with the device
        print("Installing rule on device %s", uri);
        String res = app.setConfigTables(device.id(), table, action, criteria, fields_keys, keys, args_fields, args);

        if(res != null){
            print("A problem occured\n");
            print(res);
        } 
    }

}
