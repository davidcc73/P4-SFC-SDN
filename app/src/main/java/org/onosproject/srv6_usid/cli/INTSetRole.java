
package org.onosproject.srv6_usid.cli;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;

import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.srv6_usid.INTComponent;



/**
 *  INT Transit Insert Command
 */
@Service
@Command(scope = "onos", name = "INT_Role-set",
        description = "Reads the file at config/INT_Tables/ exclusive for each device, to insert the role/rules that each INT device needs to operate using INT")
public class INTSetRole extends AbstractShellCommand{

    //calling the name on the cli will push all the rules at INT/Tables rx.txt rules to the respective devices
    @Override
    protected void doExecute() {
        DeviceService deviceService = get(DeviceService.class);
        INTComponent app = get(INTComponent.class);

        print("Setting INT roles for all devices...");
        for(int num = 1; num <= 5; num++) {
            String filename = "/config/INT_Tables/s" + num + ".txt";
            String uri = "device:s" + num;
            String result="placeholder";
            String pipeline, table, action, control, arg_str;
            int key, arg;
            String[] parts, tableParts;

            String line = null;
            Device device = deviceService.getDevice(DeviceId.deviceId(uri));

            if (device == null) {
                    print("Device \"%s\" is not found", uri);
                    continue;
            }

            //open the file and peer each line individually do a call
            try (BufferedReader br = new BufferedReader(new FileReader(filename))) {
                while ((line = br.readLine()) != null) {
                    if(line.startsWith("//") || line.trim().isEmpty()){continue;}   
                    parts = line.split("\\s+");
                    if (parts[0].equals("mirroring_add")) {
                        int sessionID = Integer.parseInt(parts[1]);
                        long port = Long.parseLong(parts[2]);
                        //print("Installing rule on device %s", uri);
                        result = app.createMirroingSession(device.id(), sessionID,  port);

                    } else if (parts[0].equals("table_set_default")) {
                        tableParts = parts[1].split("\\.");
                        pipeline = tableParts[0];
                        control = tableParts[1];
                        table = tableParts[2];
                        action = parts[2];
                        arg = Integer.parseInt(parts[3]);
                        //print("Installing rule on device %s", uri);
                        result = app.insertDefaultTableRule(device.id(), pipeline, control, table, arg, action);

                    } else if (parts[0].equals("INT_table_add")) {
                        tableParts = parts[1].split("\\.");
                        pipeline = tableParts[0];
                        control = tableParts[1];
                        table = tableParts[2];
                        action = parts[2];
                        if(table.equals("tb_set_source") || table.equals("tb_set_sink")){ 
                            key = Integer.parseInt(parts[3]);
                            result = app.insertRule_process_int_source_sink(device.id(), pipeline, control, table, action, key);
                        }
                        else if(table.equals("tb_generate_report")){
                            key = Integer.parseInt(parts[3]);
                            parts = line.split("=>");   
                            arg_str = parts[1];
                            result = app.insertRule_process_int_report(device.id(), pipeline, control, table, action, key, arg_str);
                        }
                        else if(table.equals("tb_int_source")){
                            String[] keys = {parts[3], parts[4], parts[5], parts[6]}; 
                            String[] args = {parts[8], parts[9], parts[10], parts[11]};  
                            result = app.insertRule_process_int_source(device.id(), pipeline, control, table, action, keys, args);
                        }
                        else{
                            print("ERROR: table_add not supported for table %s", table);
                            continue;
                        }
                        //print("Installing rule on device %s", uri);
                    } else {
                        System.out.println("Unsupported operation at file: " + filename + " operation: " + parts[0]);
                        continue;
                    }
                    if(result != "Success"){print(result);}
                }
            } catch (FileNotFoundException e) {
                print("File not found for device %s", uri);
                print(e.getMessage());
                continue;
            } catch (IOException e) {
                print("Error acessing the existing file for %s", uri);
                e.printStackTrace(); 
                continue;
            } catch (Exception e) {
                print("ERROR on file for %s and line: %s", uri, line);
                e.printStackTrace();
                continue; 
            }
        }
    }
}
