
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
import org.onosproject.srv6_usid.INTComponent;


/**
 *  INT Transit Insert Command
 */
@Service
@Command(scope = "onos", name = "INT_Transit-insert",
        description = "Insert a INT instructions into the Transit table")
public class INTTransitInsert extends AbstractShellCommand {
//pipeline     control    table   key    action   cmp_field_on_p4    cmp_criteria
        @Argument(index = 0, name = "pipeline", 
                description = "pipeline with the control block",
                required = true, multiValued = false)
        @Completion(DeviceIdCompleter.class)
        String pipeline = null;

        @Argument(index = 1, name = "control", 
                description = "control with the table",
                required = true, multiValued = false)
        @Completion(DeviceIdCompleter.class)
        String control = null;

        @Argument(index = 2, name = "table", 
                description = "table to insert the rule into",
                required = true, multiValued = false)
        @Completion(DeviceIdCompleter.class)
        String table = null;

        @Argument(index = 3, name = "key",
                description = "key value",
                required = true, multiValued = false)
        String key = null;

        @Argument(index = 4, name = "action",
                description = "action name",
                required = true, multiValued = false)
        String action = null;

        @Argument(index = 5, name = "cmp_field_on_p4",
                description = "name of the comparasion field on the p4 table",
                required = true, multiValued = false)
        String cmp_field_on_p4 = null;

        @Argument(index = 6, name = "cmp_criteria",
                description = "comparasion criteria used on the p4 table match",
                required = true, multiValued = false)
        String cmp_criteria = null;

        @Override
        protected void doExecute() {
                String result = null;
                DeviceService deviceService = get(DeviceService.class);
                INTComponent app = get(INTComponent.class);

                print("Inserting INT rule into the Transit table...");
                for(int num = 1; num <= 5; num++) {
                        String uri = "device:s" + num;
                        Device device = deviceService.getDevice(DeviceId.deviceId(uri));

                        int intValue = Integer.parseInt(key.substring(2), 16);

                        if (device == null) {
                                print("Device \"%s\" is not found", uri);
                                continue;
                        }

                        //print("Installing rule on device %s", uri);
                        result = app.insertINT_Rule(device.id(), pipeline, control, table, action, 
                                                   intValue, null, 
                                                   cmp_field_on_p4, cmp_criteria);
                        if(result != "Success"){print(result);}
                }
        }
}
