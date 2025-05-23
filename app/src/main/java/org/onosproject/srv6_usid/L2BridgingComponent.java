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

import org.onlab.packet.MacAddress;
import org.onosproject.core.ApplicationId;
import org.onosproject.mastership.MastershipService;
import org.onosproject.net.ConnectPoint;
import org.onosproject.net.DeviceId;
import org.onosproject.net.Host;
import org.onosproject.net.PortNumber;
import org.onosproject.net.config.NetworkConfigService;
import org.onosproject.net.device.DeviceEvent;
import org.onosproject.net.device.DeviceListener;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.net.flow.criteria.PiCriterion;
import org.onosproject.net.group.GroupDescription;
import org.onosproject.net.group.GroupService;
import org.onosproject.net.host.HostEvent;
import org.onosproject.net.host.HostListener;
import org.onosproject.net.host.HostService;
import org.onosproject.net.intf.Interface;
import org.onosproject.net.intf.InterfaceService;
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

import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

import static org.onosproject.srv6_usid.AppConstants.INITIAL_SETUP_DELAY;

/**
 * App component that configures devices to provide L2 bridging capabilities.
 */
@Component(
        immediate = true,
        enabled = true,
        service = L2BridgingComponent.class
)
public class L2BridgingComponent {

    private final Logger log = LoggerFactory.getLogger(getClass());

    private static final int DEFAULT_BROADCAST_GROUP_ID = 255;            //all hosts
    private static final String all_hosts_mcas_address = "ff:ff:ff:ff:ff:ff";
    private static final int ethernet_full_mask_length = 48;

    private final DeviceListener deviceListener = new InternalDeviceListener();
    private final HostListener hostListener = new InternalHostListener();

    private ApplicationId appId;

    //--------------------------------------------------------------------------
    // ONOS CORE SERVICE BINDING
    //
    // These variables are set by the Karaf runtime environment before calling
    // the activate() method.
    //--------------------------------------------------------------------------

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private HostService hostService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private DeviceService deviceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private InterfaceService interfaceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private NetworkConfigService configService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private FlowRuleService flowRuleService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private GroupService groupService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private MastershipService mastershipService;

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

        // Register listeners to be informed about device and host events.
        deviceService.addListener(deviceListener);
        hostService.addListener(hostListener);
        // Schedule set up of existing devices. Needed when reloading the app.
        mainComponent.scheduleTask(this::setUpAllDevices, INITIAL_SETUP_DELAY);

        log.info("Started");
    }

    @Deactivate
    protected void deactivate() {
        deviceService.removeListener(deviceListener);
        hostService.removeListener(hostListener);

        log.info("Stopped");
    }

    /**
     * Sets up everything necessary to support L2 bridging on the given device.
     *
     * @param deviceId the device to set up
     */
    private void setUpDevice(DeviceId deviceId) {
        insertManagementMulticastGroup(deviceId);
        insertManagementMulticastFlowRules(deviceId);
    }

    /**
     * Creates a flow rule to match packets with a given MAC address and masl length and
     * forward them to a multicast group.
     *
     * 
     * ALL IT DOES CAN BE REPLICATED BY A TABLE RULE INSERTION FUNCTION
     * AS, LIKE THE CLI COMMAND "table_add"
     *
     * @param deviceId the device where to install the rule
     * @param mcast_group the multicast group to which the packets are forwarded
     * @param mac_key the MAC address to match
     * @param mask_length the mask length to apply to the MAC address
     */
    private void createMcastTableRule(DeviceId deviceId, int mcast_group, String mac_key, int mask_length){

        //Broadcast to all hosts, including ARP pkt
        final PiCriterion macBroadcastCriterion = PiCriterion.builder()
        .matchLpm(
                PiMatchFieldId.of("hdr.ethernet.dstAddr"),
                MacAddress.valueOf(mac_key).toBytes(),
                mask_length)
        .build();

        // Action: set multicast group id (the same used )
        final PiAction setMcastGroupAction = PiAction.builder()
                .withId(PiActionId.of("MyIngress.set_multicast_group"))
                .withParameter(new PiActionParam(
                        PiActionParamId.of("gid"),
                        mcast_group))
                .build();

        //  Build 1 flow rule.
        final String tableId = "MyIngress.multicast";

        final FlowRule rule1 = Utils.buildFlowRule(
                deviceId, appId, tableId,
                macBroadcastCriterion, setMcastGroupAction);
                
        // Insert rules.
        flowRuleService.applyFlowRules(rule1);
    }

    /**
     * In a given device, creates the multicast group, and ports to said group.
     * 
     * IF GROUP ALREADY EXISTS, NO CHANGES CAN BE MADE TO IT, NO ERROR MSG WILL BE RETURNED FOR THIS CASE 
     * 
     * @param deviceId the device where to install the group, if not existing already
     * @param mcast_group the multicast group to which the ports are added
     * @param ports the ports to be added to the multicast group
     */
    public String addMcastGroupAndPorts(DeviceId deviceId, int mcast_group, int[] ports_arrya) {

        // Replicate packets to given ports at ports_arrya
        Set<PortNumber> ports = new HashSet<>();
        for (int port : ports_arrya) {
            ports.add(PortNumber.portNumber(port));
        }

        if (ports.isEmpty()) {
            log.warn("Device {} No valid port number given", deviceId);
            return "No valid port number given";
        }

        log.info("Adding L2 multicast group with {} ports on {}...",
                    ports.size(), deviceId);

        // Forge group object.
        final GroupDescription multicastGroup = Utils.buildMulticastGroup(
                appId, deviceId, mcast_group, ports);

        // Insert.
        groupService.addGroup(multicastGroup);

        return null;
    }

    /**
     * Inserts an ALL ports from a device (at netcfg.json), to the
     * management mcast group to replicate packets to all network elements. 
     * This multicast group will be used to do broadcasts
     * <p>
     * ALL groups in ONOS are equivalent to P4Runtime packet replication engine
     * (PRE) Multicast groups.
     *
     * @param deviceId the device where to install the group
     */
    private void insertManagementMulticastGroup(DeviceId deviceId) {

        // Replicate packets where we know hosts are attached.
        Set<PortNumber> ports = getHostFacingPorts(deviceId);

        if (ports.isEmpty()) {
            // Stop here.
            log.warn("Device {} has 0 host facing ports", deviceId);
            return;
        }

        log.info("Adding L2 multicast group with {} ports on {}...",
                 ports.size(), deviceId);

        // Forge group object.
        final GroupDescription multicastGroup = Utils.buildMulticastGroup(
                appId, deviceId, DEFAULT_BROADCAST_GROUP_ID, ports);

        // Insert.
        groupService.addGroup(multicastGroup);
    }

    /**
     * Insert flow rules matching matching ethernet destination
     * broadcast/multicast addresses (e.g. ARP requests, NDP Neighbor
     * Solicitation, etc.). Such packets should be processed by the multicast
     * group created before.
     * <p>
     * This method will be called at component activation for each device
     * (switch) known by ONOS, and every time a new device-added event is
     * captured by the InternalDeviceListener defined below.
     * 
     * @param deviceId device ID where to install the rules
     */
    private void insertManagementMulticastFlowRules(DeviceId deviceId) {
        log.info("Adding L2 multicast rules on {}...", deviceId);
        createMcastTableRule(deviceId, DEFAULT_BROADCAST_GROUP_ID, all_hosts_mcas_address, ethernet_full_mask_length);
    }

    /**
     * Insert flow rules to forward packets to a given host located at the given
     * device and port. 
     * Based on layer L2, to each switch maps the neighours mac to our ports connected to it.
     * <p>
     * This method will be called at component activation for each host known by
     * ONOS, and every time a new host-added event is captured by the
     * InternalHostListener defined below.
     *
     * @param host     host instance
     * @param deviceId device where the host is located
     * @param port     port where the host is attached to
     */
    private void learnHost(Host host, DeviceId deviceId, PortNumber port) {

        log.info("Adding L2 unicast rule on {} for host {} (port {})...",
                 deviceId, host.id(), port);

        final String tableId = "MyIngress.unicast";
        // Match exactly on the host MAC address.
        final MacAddress hostMac = host.mac();
        final PiCriterion hostMacCriterion = PiCriterion.builder()
                .matchExact(PiMatchFieldId.of("hdr.ethernet.dstAddr"),
                            hostMac.toBytes())
                .build();

        // Action: set output port
        final PiAction l2UnicastAction = PiAction.builder()
                .withId(PiActionId.of("MyIngress.set_egress_port"))
                .withParameter(new PiActionParam(
                        PiActionParamId.of("port"),
                        port.toLong()))
                .build();

        // Forge flow rule.
        final FlowRule rule = Utils.buildFlowRule(
                deviceId, appId, tableId, hostMacCriterion, l2UnicastAction);

        // Insert.
        flowRuleService.applyFlowRules(rule);
    }

    //--------------------------------------------------------------------------
    // EVENT LISTENERS
    //
    // Events are processed only if isRelevant() returns true.
    //--------------------------------------------------------------------------

    /**
     * Listener of device events.
     */
    public class InternalDeviceListener implements DeviceListener {

        @Override
        public boolean isRelevant(DeviceEvent event) {
            switch (event.type()) {
                case DEVICE_ADDED:
                case DEVICE_AVAILABILITY_CHANGED:
                    break;
                default:
                    // Ignore other events.
                    return false;
            }
            // Process only if this controller instance is the master.
            return true;
        }

        @Override
        public void event(DeviceEvent event) {
            final DeviceId deviceId = event.subject().id();
            if (deviceService.isAvailable(deviceId)) {
                // A P4Runtime device is considered available in ONOS when there
                // is a StreamChannel session open and the pipeline
                // configuration has been set.

                // Events are processed using a thread pool defined in the
                // MainComponent.
                mainComponent.getExecutorService().execute(() -> {
                    log.info("{} event! deviceId={}", event.type(), deviceId);

                    setUpDevice(deviceId);
                });
            }
        }
    }

    /**
     * Listener of host events.
     */
    public class InternalHostListener implements HostListener {

        @Override
        public boolean isRelevant(HostEvent event) {
            switch (event.type()) {
                case HOST_ADDED:
                    // Host added events will be generated by the
                    // HostLocationProvider by intercepting ARP/NDP packets.
                    break;
                case HOST_REMOVED:
                case HOST_UPDATED:
                case HOST_MOVED:
                default:
                    // Ignore other events.
                    // Food for thoughts: how to support host moved/removed?
                    return false;
            }
            // Process host event only if this controller instance is the master
            // for the device where this host is attached to.
            return true;
        }

        @Override
        public void event(HostEvent event) {
            final Host host = event.subject();
            // Device and port where the host is located.
            final DeviceId deviceId = host.location().deviceId();
            final PortNumber port = host.location().port();

            mainComponent.getExecutorService().execute(() -> {
                log.info("{} event! host={}, deviceId={}, port={}",
                         event.type(), host.id(), deviceId, port);

                learnHost(host, deviceId, port);
            });
        }
    }

    //--------------------------------------------------------------------------
    // UTILITY METHODS
    //--------------------------------------------------------------------------

    /**
     * Returns a set of ports for the given device that are used to connect
     * hosts to the fabric.
     *
     * @param deviceId device ID
     * @return set of host facing ports
     */
    private Set<PortNumber> getHostFacingPorts(DeviceId deviceId) {
        // Get all interfaces configured via netcfg for the given device ID and return the corresponding device port number. 
        // Interface configuration in the netcfg.json looks like this:
        // "device:leaf1/3": {
        //   "interfaces": [
        //     {
        //       "name": "leaf1-3",
        //       "ips": ["2001:1:1::ff/64"]
        //     }
        //   ]
        // }

        // The ports were configured in a way that each switch will circulate the packets through their outer links
        // with exception of 1, to avoid a broadcasting loop.
        // The broadcast ports were configured so that each link works on both directions.

        return interfaceService.getInterfaces().stream()            //gets all interfaces
                .map(Interface::connectPoint)                       //converts them to ConnectPoint
                .filter(cp -> cp.deviceId().equals(deviceId))       //only the ones for the given device
                .map(ConnectPoint::port)                            //converts them to port number
                .collect(Collectors.toSet());                       //aggregates them in a set
    }

    /**
     * Sets up L2 bridging on all devices known by ONOS and for which this ONOS
     * node instance is currently master.
     * <p>
     * This method is called at component activation, with a delay.
     */
    private void setUpAllDevices() {
        deviceService.getAvailableDevices().forEach(device -> {
            if (mastershipService.isLocalMaster(device.id())) {
                log.info("*** L2 BRIDGING - Starting initial set up for {}...", device.id());
                setUpDevice(device.id());
                // For all hosts connected to this device...
                hostService.getConnectedHosts(device.id()).forEach(
                        host -> learnHost(host, host.location().deviceId(),
                                          host.location().port()));
            }
        });
    }
}
