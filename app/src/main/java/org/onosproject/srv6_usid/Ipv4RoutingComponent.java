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

package org.onosproject.srv6_usid;

import com.google.common.collect.Lists;

import org.onlab.packet.IpAddress;
import org.onlab.packet.MacAddress;
import org.onlab.util.ItemNotFoundException;
import org.onosproject.core.ApplicationId;
import org.onosproject.mastership.MastershipService;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.Link;
import org.onosproject.net.PortNumber;
import org.onosproject.net.config.NetworkConfigService;
import org.onosproject.net.device.DeviceEvent;
import org.onosproject.net.device.DeviceListener;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.TableId;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.net.flow.criteria.PiCriterion;
import org.onosproject.net.group.GroupService;
import org.onosproject.net.intf.InterfaceService;
import org.onosproject.net.link.LinkEvent;
import org.onosproject.net.link.LinkListener;
import org.onosproject.net.link.LinkService;
import org.onosproject.net.pi.model.PiTableId;
import org.onosproject.net.pi.model.PiActionId;
import org.onosproject.net.pi.model.PiActionParamId;
import org.onosproject.net.pi.model.PiMatchFieldId;
import org.onosproject.net.pi.runtime.PiAction;
import org.onosproject.net.pi.runtime.PiAction.Builder;
import org.onosproject.net.pi.runtime.PiActionParam;
import org.onosproject.net.pi.runtime.PiTableAction;
import org.onosproject.net.flow.DefaultFlowRule;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Reference;
import org.osgi.service.component.annotations.ReferenceCardinality;
import org.onosproject.srv6_usid.common.Srv6DeviceConfig;
import org.onosproject.srv6_usid.common.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.Optional;
import java.util.List;
import java.util.Set;
import java.net.InetAddress;
import java.net.UnknownHostException;

import java.util.stream.StreamSupport;

import static org.onosproject.srv6_usid.AppConstants.INITIAL_SETUP_DELAY;


/**
 * App component that configures devices to provide IPv4 routing capabilities
 * across the whole fabric.
 */
@Component(
        immediate = true,
        // TODO EXERCISE 3
        // set to true when ready
        enabled = true,
        service = Ipv4RoutingComponent.class
)
public class Ipv4RoutingComponent{

    private static final Logger log = LoggerFactory.getLogger(Ipv4RoutingComponent.class);

    private final LinkListener linkListener = new InternalLinkListener();
    private final DeviceListener deviceListener = new InternalDeviceListener();

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
    private MastershipService mastershipService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private GroupService groupService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private DeviceService deviceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private NetworkConfigService networkConfigService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private InterfaceService interfaceService;

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

        linkService.addListener(linkListener);
        deviceService.addListener(deviceListener);

        // Schedule set up for all devices.
        mainComponent.scheduleTask(this::setUpAllDevices, INITIAL_SETUP_DELAY);  //commented so setnextl2 could change, and is not needed, the topology is received at runtime via onos cli

        log.info("Started");
    }

    @Deactivate
    protected void deactivate() {
        linkService.removeListener(linkListener);
        deviceService.removeListener(deviceListener);

        log.info("Stopped");
    }

    /**
     * Creates a flow rule for the L2 table mapping the given next hop MAC to
     * the given output port.
     * <p>
     * This is called by the routing policy methods below to establish L2-based
     * forwarding inside the fabric, e.g., when deviceId is a leaf switch and
     * nextHopMac is the one of a core switch.
     *
     * @param deviceId   the device
     * @param nexthopMac the next hop (destination) mac
     * @param outPort    the output port
     */
    private FlowRule createL2NextHopRule(DeviceId deviceId, MacAddress nexthopMac,
                                         PortNumber outPort) {   //maps next MAC to Out Port

        final String tableId = "MyIngress.unicast";
        final PiCriterion match = PiCriterion.builder()
                .matchExact(PiMatchFieldId.of("hdr.ethernet.dstAddr"),
                            nexthopMac.toBytes())
                .build();


        final PiAction action = PiAction.builder()
                .withId(PiActionId.of("MyIngress.set_egress_port"))
                .withParameter(new PiActionParam(
                        PiActionParamId.of("port"),
                        outPort.toLong()))
                .build();

        return Utils.buildFlowRule(
                deviceId, appId, tableId, match, action);
    }

    /**
     * @param deviceId the device ID
     */
    public String setConfigTables(DeviceId deviceId, String tableId, String action, 
                                String[] criterias, 
                                String[] fields_keys, String[] keys, 
                                String[] args_fields, String[] args, Integer priority) {
        PiCriterion match = null;        
        PiActionParam param = null;
        List<PiActionParam> actionParams = Lists.newArrayList();
        Builder builder = PiAction.builder().withId(PiActionId.of(action));
        PiCriterion.Builder builder_match = PiCriterion.builder();

        byte[] key;
        int prefix_int = -1;
        String key_string = "";

        log.info("Adding Config rule to {}...", deviceId);

        //-------------------------------------Match
        if(fields_keys != null && keys != null) {
            for(int i = 0; i < fields_keys.length; i++) {
                if(criterias[i].equals("LPM") || criterias[i].equals("TERNARY")) {
                    String[] aux = keys[i].split("-");
                    key_string = aux[0];
                    prefix_int = Integer.valueOf(aux[1]);
                }

                if(criterias[i].equals("LPM")) {
                    if(key_string.contains(":")){                 //only to match 1 MAC 
                        MacAddress mac = MacAddress.valueOf(key_string);
                        key = mac.toBytes();
                    }
                    else if(key_string.contains(".")){            //only to match 1 IPv4
                        IpAddress ip = IpAddress.valueOf(key_string);
                        key = ip.toOctets();
                    }
                    else{
                        return "Given key is not IP nor MAC" + key_string;
                    }
                    builder_match = builder_match
                            .matchLpm(
                                PiMatchFieldId.of(fields_keys[i]),
                                key,
                                prefix_int);

                }else if(criterias[i].equals("EXACT")) {         //only to match x Integers or Macs
                    if(keys[i].contains(":")){                  //either mac
                        MacAddress mac = MacAddress.valueOf(keys[i]);
                        key = mac.toBytes();
                        builder_match = builder_match
                            .matchExact(
                                PiMatchFieldId.of(fields_keys[i]),
                                key);
                    }
                    else{                                       // or integer   
                        builder_match = builder_match
                            .matchExact(
                                PiMatchFieldId.of(fields_keys[i]),
                                Integer.valueOf(keys[i]));
                    }
                }
                else if(criterias[i].equals("TERNARY")) {        //only to match x Integers       
                    builder_match = builder_match
                        .matchTernary(
                            PiMatchFieldId.of(fields_keys[i]),
                            Integer.valueOf(key_string),
                            prefix_int);
                }
            }
        }
        match = builder_match.build();     

        //-------------------------------------Arguments
        if(args_fields != null && args != null) {
            for(int i = 0; i < args_fields.length; i++) {
                if(args[i].contains(":")){                      //either mac
                    param = new PiActionParam(PiActionParamId.of(args_fields[i]), MacAddress.valueOf(args[i]).toBytes());
                }
                else if(args[i].contains(".")){                 //IPv4
                    try {
                        param = new PiActionParam(PiActionParamId.of(args_fields[i]), InetAddress.getByName(args[i]).getAddress());
                    }catch (UnknownHostException e) {
                        log.error("Invalid IPv4 address: {}", args[i], e);
                        return "ERROR IPv4 conversion: SEE ONOS LOGS";
                    }
                }
                else {                                          // or integer
                    param = new PiActionParam(PiActionParamId.of(args_fields[i]), Integer.valueOf(args[i]));
                }
                
                actionParams.add(param);       
            }
        }

        builder = builder.withParameters(actionParams);
        PiTableAction tableAction = builder.build();

        //Manual FlowRule creation so we can set priority
        final FlowRule Rule = DefaultFlowRule.builder()
            .forDevice(deviceId)
            .forTable(PiTableId.of(tableId))
            .withSelector(DefaultTrafficSelector.builder().matchPi(match).build())
            .withTreatment(DefaultTrafficTreatment.builder().piTableAction(tableAction).build())
            .withPriority(priority)     // Set priority here
            .fromApp(appId)
            .makePermanent()            // Or use .makeTemporary(timeout) if needed
            .build();
        
        //log.info("Rule: {}", Rule);

        flowRuleService.applyFlowRules(Rule);
        return null;
    }


    //--------------------------------------------------------------------------
    // EVENT LISTENERS
    //
    // Events are processed only if isRelevant() returns true.
    //--------------------------------------------------------------------------

    /**
     * Listener of link events, which triggers configuration of routing rules to
     * forward packets across the fabric, i.e. from leaves to cores and vice
     * versa.
     * <p>
     * Reacting to link events instead of device ones, allows us to make sure
     * all device are always configured with a topology view that includes all
     * links, e.g. modifying an ECMP group as soon as a new link is added. The
     * downside is that we might be configuring the same device twice for the
     * same set of links/paths. However, the ONOS core treats these cases as a
     * no-op when the device is already configured with the desired forwarding
     * state (i.e. flows and groups)
     */
    class InternalLinkListener implements LinkListener {

        @Override
        public boolean isRelevant(LinkEvent event) {
            switch (event.type()) {
                case LINK_ADDED:
                    break;
                case LINK_UPDATED:              //maybe useful for when links break
                case LINK_REMOVED:
                log.info("event! ... info={}", event);
                default:
                    return false;
            }
            DeviceId srcDev = event.subject().src().deviceId();
            DeviceId dstDev = event.subject().dst().deviceId();
            return mastershipService.isLocalMaster(srcDev) ||
                    mastershipService.isLocalMaster(dstDev);
        }

        @Override
        public void event(LinkEvent event) {    //see isRelevant() explanation
            DeviceId srcDev = event.subject().src().deviceId();
            DeviceId dstDev = event.subject().dst().deviceId();

            // Being a new link discovered we need to map the MAC of the new devices to their own outports
            if (mastershipService.isLocalMaster(srcDev)) {
                mainComponent.getExecutorService().execute(() -> {
                    log.info("{} event! Configuring {}... linkSrc={}, linkDst={}",
                             event.type(), srcDev, srcDev, dstDev);
                    setUpL2NextHopRules(srcDev);
                });
            }
            if (mastershipService.isLocalMaster(dstDev)) {
                mainComponent.getExecutorService().execute(() -> {
                    log.info("{} event! Configuring {}... linkSrc={}, linkDst={}",
                             event.type(), dstDev, srcDev, dstDev);
                    setUpL2NextHopRules(dstDev);
                });
            }
        }
    }

    /**
     * Listener of device events which triggers configuration of the My Station
     * table.
     */
    class InternalDeviceListener implements DeviceListener {

        @Override
        public boolean isRelevant(DeviceEvent event) {
            switch (event.type()) {
                case DEVICE_AVAILABILITY_CHANGED:
                case DEVICE_ADDED:
                    break;
                default:
                    return false;
            }
            // Process device event if this controller instance is the master
            // for the device and the device is available.
            DeviceId deviceId = event.subject().id();
            return mastershipService.isLocalMaster(deviceId) &&
                    deviceService.isAvailable(event.subject().id());
        }

        @Override
        public void event(DeviceEvent event) {
            mainComponent.getExecutorService().execute(() -> {
                DeviceId deviceId = event.subject().id();
                log.info("{} event! device id={}", event.type(), deviceId);
            });
        }
    }

    //--------------------------------------------------------------------------
    // ROUTING POLICY METHODS
    //
    // Called by event listeners, these methods implement the actual routing
    // policy, responsible of computing paths and creating ECMP groups.
    //--------------------------------------------------------------------------

    /**
     * Set up L2 nexthop rules of a device to providing forwarding inside the
     * fabric
     *
     * @param deviceId the device ID
     */
    private void setUpL2NextHopRules(DeviceId deviceId) {

        Set<Link> egressLinks = linkService.getDeviceEgressLinks(deviceId);

        for (Link link : egressLinks) {
            // For each other switch directly connected to this.
            final DeviceId nextHopDevice = link.dst().deviceId();
            // Get port of this device connecting to next hop.
            final PortNumber outPort = link.src().port();
            // Get next hop MAC address.
            final MacAddress nextHopMac = getMyStationMac(nextHopDevice);

            if (nextHopMac == null) {
                log.warn("Could not find MAC address for next hop device {}", nextHopDevice);
            } else {
                // Create L2 forwarding rule or handle the next hop information as needed.
                final FlowRule nextHopRule = createL2NextHopRule(deviceId, nextHopMac, outPort);
        
                flowRuleService.applyFlowRules(nextHopRule);

                log.info("Device {} has next hop {} via port {} with MAC {}",
                        deviceId, nextHopDevice, outPort, nextHopMac);

            }
        }
    }

    //--------------------------------------------------------------------------
    // UTILITY METHODS
    //--------------------------------------------------------------------------

    /**
     * Sets up IPv4 routing on all devices known by ONOS and for which this ONOS
     * node instance is currently master.
     */
    private synchronized void setUpAllDevices() {       //acivated at this component boot
        // Set up host routes
        StreamSupport.stream(deviceService.getAvailableDevices().spliterator(), false)   //not sure if correct
                .map(Device::id)
                .filter(mastershipService::isLocalMaster)
                .forEach(deviceId -> {
                    log.info("*** IPV4 ROUTING - Starting initial set up for {}...", deviceId);
                    setUpL2NextHopRules(deviceId);
                });
    }

    /**
     * Returns the MAC address configured in the "myStationMac" property of the
     * given device config.
     *
     * @param deviceId the device ID
     * @return MyStation MAC address
     */
    private MacAddress getMyStationMac(DeviceId deviceId) {
        return getDeviceConfig(deviceId)
                .map(Srv6DeviceConfig::myStationMac)
                .orElseThrow(() -> new ItemNotFoundException(
                        "Missing myStationMac config for " + deviceId));
    }
    
    /**
     * Returns the IP address configured in the "subNetIP" property of the
     * given device config.
     *
     * @param deviceId the device ID
     * @return MyStation MAC address
     */
    private IpAddress getMySubNetIP(DeviceId deviceId) {
        return getDeviceConfig(deviceId)
                .map(Srv6DeviceConfig::mySubNetIP)
                .orElseThrow(() -> new ItemNotFoundException(
                        "Missing mySubNetIP config for " + deviceId));
    }

    /**
     * Returns the Srv6 config object for the given device.
     *
     * @param deviceId the device ID
     * @return Srv6  device config
     */
    private Optional<Srv6DeviceConfig> getDeviceConfig(DeviceId deviceId) {
        Srv6DeviceConfig config = networkConfigService.getConfig(
                deviceId, Srv6DeviceConfig.class);
        return Optional.ofNullable(config);
    }

}
