package org.onosproject.srv6_usid;

import java.math.BigInteger;
import java.net.Inet6Address;
import java.net.InetAddress;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.nio.ByteBuffer;

import org.onlab.packet.IpAddress;
import org.onlab.packet.MacAddress;
import org.onosproject.core.ApplicationId;
import org.onosproject.net.DeviceId;
import org.onosproject.net.PortNumber;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.net.flow.criteria.PiCriterion;
import org.onosproject.net.flow.criteria.PiCriterion.Builder;
import org.onosproject.net.group.GroupDescription;
import org.onosproject.net.group.GroupService;
import org.onosproject.net.link.LinkService;
import org.onosproject.net.pi.model.PiActionId;
import org.onosproject.net.pi.model.PiActionParamId;
import org.onosproject.net.pi.model.PiMatchFieldId;
import org.onosproject.net.pi.runtime.PiAction;
import org.onosproject.net.pi.runtime.PiActionParam;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Reference;
import org.osgi.service.component.annotations.ReferenceCardinality;
import org.onosproject.srv6_usid.common.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.collect.Lists;


/**
 * App component that configures devices to provide INT capabilities
 * across the whole fabric.
 */
@Component(
        immediate = true,
        enabled = true,
        service = INTComponent.class
)
public class INTComponent {

        private static final Logger log = LoggerFactory.getLogger(INTComponent.class);

        //private final LinkListener linkListener = new InternalLinkListener();
        //private final DeviceListener deviceListener = new InternalDeviceListener();

        private ApplicationId appId;

        //--------------------------------------------------------------------------
        // ONOS CORE SERVICE BINDING
        //
        // These variables are set by the Karaf runtime environment before calling
        // the activate() method.
        //--------------------------------------------------------------------------

        @Reference(cardinality = ReferenceCardinality.MANDATORY)
        private FlowRuleService flowRuleService;

        @Reference(cardinality = ReferenceCardinality.MANDATORY)
        private GroupService groupService;

        @Reference(cardinality = ReferenceCardinality.MANDATORY)
        private DeviceService deviceService;

        @Reference(cardinality = ReferenceCardinality.MANDATORY)
        private LinkService linkService;

        @Reference(cardinality = ReferenceCardinality.MANDATORY)
        private MainComponent mainComponent;

        //--------------------------------------------------------------------------
        // COMPONENT ACTIVATION.
        //
        // When loading/unloading the app the Karaf runtime environment will call
        // activate()/deactivate().
        //--------------------------------------------------------------------------

        @Activate
        protected void activate() {
                appId = mainComponent.getAppId();

                // linkService.addListener(linkListener);
                // deviceService.addListener(deviceListener);

                // Schedule set up for all devices.
                // mainComponent.scheduleTask(this::setUpAllDevices, INITIAL_SETUP_DELAY);

                log.info("Started");
        }

        @Deactivate
        protected void deactivate() {
                //linkService.removeListener(linkListener);
                //deviceService.removeListener(deviceListener);

                log.info("Stopped");
        }


        /**
         * Creates a rule INT Transit rule about wich info to collect
         * <p>
         * function called by INTTransitInsert command
         *
         * @param deviceId       the device
         * @param pipeline       the pipeline name containing the control block
         * @param control        the control containing the action/table
         * @param table          the table
         * @param action_name    action to be triggered
         * @param key_value      key to be matche
         * @param arg_value      arg used by the action
         * @param cmp_field      the comparison field used on the p4 table match
         * @param cmp_criteria   the comparison criteria used on the p4 table match

         */
        public String insertINT_Rule(DeviceId deviceId, String pipeline, String control, String table, String action_name, 
                                    int key_value,    String arg_value, 
                                    String cmp_field, String cmp_criteria) {
                String result = null;
                String tableId = pipeline + "." + control + "." + table;
                final PiCriterion match;

                final PiAction action = PiAction.builder()
                        .withId(PiActionId.of(pipeline + "." + control + "." + action_name))
                        .build();

                if(cmp_criteria.equals("exact")){
                        match = PiCriterion.builder()
                        .matchExact(PiMatchFieldId.of(cmp_field), key_value)
                        .build();
                }
                else{
                        log.info("Unsoported comparasion criteria:"+cmp_criteria); 
                        return("Error: Unsupported comparasion criteria");
                }

                try{
                        //log.info("Pushing INT rule to device {}", deviceId);  
                        
                        final FlowRule rule = Utils.buildFlowRule(deviceId, appId, tableId, match, action);
                        flowRuleService.applyFlowRules(rule);
                        
                        result = "Success";        
                }
                catch(Exception e){
                        log.info("Error pushing INT Transit rule to device {}:\n {}", deviceId, e);
                        result = "Something went wrong, see ONOS logs for more details"; 
                }
                return result;
        }
        
        public String createMirroingSession(DeviceId deviceId, int session_ID, long port){
                log.info("Pushing Mirroing Session to device:{}", deviceId);

                try {
                        Collection<PortNumber> list_ports = new ArrayList<>();
                        list_ports.add(PortNumber.portNumber(port));
                        
                        GroupDescription rule = Utils.buildCloneGroup(appId, deviceId, session_ID, list_ports);
                        groupService.addGroup(rule);
                        return "Success";
                } catch (Exception e) {
                        log.error("Error creating mirroing session for device {} Exception:{}", deviceId, e);
                        return "Error: " + e.getMessage();
                }
        }

        /**
         * Creates a rule INT Transit rule about wich info to collect
         * <p>
         * function called by INTTransitInsert command
         *
         * @param deviceId       the device
         * @param pipeline       the pipeline name containing the control block
         * @param control        the control name containing the action/table
         * @param table          the table name
         * @param arg_value      argumment to be used by the action
         * @param action_name    action to be triggered
         */
        public String insertDefaultTableRule(DeviceId deviceId, String pipeline, String control, String table, 
                                                int arg_value, String action_name) {
                //log.info("Inserting Default rule for device {} and table {}", deviceId, table);

                String tableId = pipeline + "." + control + "." + table;

                // Match a field with a wildcard value to trigger for all packets
                PiCriterion match = PiCriterion.builder()
                        .matchExact(PiMatchFieldId.of("0"), 0)
                        .build();

                PiAction action = PiAction.builder()
                        .withId(PiActionId.of(pipeline + "." + control + "." + action_name)) // Action name as specified
                        .withParameter(new PiActionParam(PiActionParamId.of("switch_id"), arg_value)) // Set action parameter
                        .build();

                try {
                        FlowRule rule = Utils.buildFlowRule(deviceId, appId, tableId, match, action);
                        flowRuleService.applyFlowRules(rule);
                        return "Success";
                } catch (Exception e) {
                        log.error("Error inserting default INT transit rule for device {}", deviceId, e);
                        return "Error: " + e.getMessage();
                }
        }

        /**
         * Creates a rule in one table (process_int_source_sink) with just one key, exact criteria and 1 arg for action
         *
         * @param deviceId       the device
         * @param pipeline       the pipeline name containing the control block
         * @param control        the control name containing the action/table
         * @param table          the table name
         * @param action_name    the action name
         * @param key            the key for the comparasion
         */
        public String insertRule_process_int_source_sink(DeviceId deviceId, String pipeline, String control, String table,
                        String action_name, int key) {
                //log.info("Inserting a table rule for device {} and table {}", deviceId, table);
                String tableId = pipeline + "." + control + "." + table;
                String cmp_field=null;

                      if(table.equals("tb_set_source")){ cmp_field="standard_metadata.ingress_port";}
                else{ if(table.equals("tb_set_sink")){   cmp_field="standard_metadata.egress_spec";}}

                PiCriterion match = PiCriterion.builder()
                        .matchExact(PiMatchFieldId.of(cmp_field), key)
                        .build();
                
                PiAction action = PiAction.builder()
                        .withId(PiActionId.of(pipeline + "." + control + "." + action_name)) // Action name as specified
                        .build();

                try {
                        FlowRule rule = Utils.buildFlowRule(deviceId, appId, tableId, match, action);
                        flowRuleService.applyFlowRules(rule);
                        return "Success";
                } catch (Exception e) {
                        log.error("Error inserting rule for device {}", deviceId, e);
                        return "Error: " + e.getMessage();
                }
        }

        /**
         * Creates a rule on table (process_int_report) with just one key, exact criteria and multiple args for action
         *
         * @param deviceId       the device
         * @param pipeline       the pipeline name containing the control block
         * @param control        the control name containing the action/table
         * @param table          the table name
         * @param action_name    the action name
         * @param key            the key for the comparasion
         * @param arg_str        the to be used bt action
         */
        public String insertRule_process_int_report(DeviceId deviceId, String pipeline, String control, String table,
                        String action_name, int key, String arg_str) {
                //log.info("Inserting a table rule for device {} and table {}", deviceId, table);
                String tableId = pipeline + "." + control + "." + table;
                PiActionParam param;
                PiActionParamId paramId;
                PiCriterion match = PiCriterion.builder()
                        .matchExact(PiMatchFieldId.of("0"), key)
                        .build();

                List<PiActionParam> actionParams = Lists.newArrayList();
                String[] args_val = arg_str.trim().split(" ");
                String[] args_name = {"src_mac", "mon_mac", "src_ip", "mon_ip", "mon_port"};
                for (int i = 0; i < args_val.length; i++) {
                        paramId = PiActionParamId.of(args_name[i]);
                             if (i==0 || i==1) param = new PiActionParam(paramId, MacAddress.valueOf(args_val[i]).toBytes());
                        else if (i==2 || i==3) param = new PiActionParam(paramId, IpAddress.valueOf(args_val[i]).toOctets());
                        else                   param = new PiActionParam(paramId, PortNumber.portNumber(args_val[i]).toLong());
                        actionParams.add(param);
                }

                PiAction.Builder actionBuilder = PiAction.builder()
                        .withId(PiActionId.of(pipeline + "." + control + "." + action_name)); // Action name as specified
                for (PiActionParam piparam : actionParams) {
                        actionBuilder = actionBuilder.withParameter(piparam);
                }

                PiAction action = actionBuilder.build();

                try {
                        FlowRule rule = Utils.buildFlowRule(deviceId, appId, tableId, match, action);
                        flowRuleService.applyFlowRules(rule);
                        return "Success";
                } catch (Exception e) {
                        log.error("Error inserting rule for device {}", deviceId, e);
                        return "Error: " + e.getMessage();
                }
        }

        /**
         * Creates a rule in one table (process_int_source) with multiple key and args, 
         *
         * @param deviceId       the device
         * @param pipeline       the pipeline name containing the control block
         * @param control        the control name containing the action/table
         * @param table          the table name
         * @param action_name    the action name
         * @param keys           the keys for the comparasion
         * @param args           the to be used by action
         */
        public String insertRule_process_int_source(DeviceId deviceId, String pipeline, String control, String table,
                                                   String action_name, String[] keys, String[] args) {
                //log.info("Inserting a table rule for device {} and table {}", deviceId, table);
                String tableId = pipeline + "." + control + "." + table;


                //MATCH ARGUMENTS
                Builder builder = PiCriterion.builder();
                String[] keys_name = {"hdr.ipv4.srcAddr", "hdr.ipv4.dstAddr", 
                                      "meta.l4_src_port", "meta.l4_dst_port"};
                for (int i = 0; i < keys.length; i++) {
                        PiMatchFieldId fieldId = PiMatchFieldId.of(keys_name[i]);
                        String[] keys_parts = keys[i].split("&&&");
                        long mask = convertMaskToLong(keys_parts[1]);
                        if(mask == 0){continue;}              //it's the "don't care" scenario
                        if (i==0 || i==1) builder.matchTernary(fieldId, convertIPv4ToLong(keys_parts[0]), mask);
                        else{
                                long ip = Integer.parseInt(keys_parts[0].substring(2), 16);
                                builder.matchTernary(fieldId, ip, mask);
                        }        
                }
                PiCriterion matchs = builder.build();


                //ACTION ARGUMENTS
                PiActionParam param;
                PiActionParamId paramId;
                List<PiActionParam> actionArgs = Lists.newArrayList();
                String[] args_name = {"hop_metadata_len", "remaining_hop_cnt", "ins_mask0003", "ins_mask0407"};
                for (int i = 0; i < args.length; i++) {
                        paramId = PiActionParamId.of(args_name[i]);

                        if(i==0 || i==1) param = new PiActionParam(paramId, Integer.parseInt(args[i]));
                        else             param = new PiActionParam(paramId, convertMaskToLong(args[i]));
                        actionArgs.add(param);
                }
                

                PiAction.Builder actionBuilder = PiAction.builder()
                        .withId(PiActionId.of(pipeline + "." + control + "." + action_name)); // Action name as specified
                for (PiActionParam piargs : actionArgs) {
                        actionBuilder = actionBuilder.withParameter(piargs);
                }
                PiAction action = actionBuilder.build();


                try {
                        FlowRule rule = Utils.buildFlowRule(deviceId, appId, tableId, matchs, action);
                        flowRuleService.applyFlowRules(rule);
                        return "Success";
                } catch (Exception e) {
                        log.error("Error inserting rule for device {}", deviceId, e);
                        return "Error: " + e.getMessage();
                }
        }

        private static long convertMaskToLong(String maskString) {
                return Long.parseLong(maskString.substring(2), 16);
        }
        private static long convertIPv6ToLong(String ipv6String) {
                try {
                        InetAddress ipv6Address = Inet6Address.getByName(ipv6String);
                        byte[] ipv6Bytes = ipv6Address.getAddress();
                        BigInteger bigInt = new BigInteger(1, ipv6Bytes);
                        return bigInt.longValue();
                } catch (Exception e) {
                        e.printStackTrace();
                        return -1; // Handle error case appropriately
                }
        }
        private static long convertIPv4ToLong(String ipv4String) {
                try {
                        InetAddress ipv4Address = InetAddress.getByName(ipv4String);
                        byte[] ipv4Bytes = ipv4Address.getAddress();
                        BigInteger bigInt = new BigInteger(1, ipv4Bytes);
                        return bigInt.longValue();
                } catch (Exception e) {
                        e.printStackTrace();
                        return -1; // Handle error case appropriately
                }
            }
}