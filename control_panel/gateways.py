# gateways.py - Implements the network gateway configuration subsystem of the
#    Byzantium control panel.

# Project Byzantium: http://wiki.hacdc.org/index.php/Byzantium
# License: GPLv3

# TODO:

# Import external modules.
import cherrypy
from mako.template import Template
from mako.lookup import TemplateLookup
from mako.exceptions import RichTraceback
import os
import os.path
import sqlite3
import subprocess

# Import core control panel modules.
from control_panel import *

# Constants.

# Classes.
# This class allows the user to turn a configured network interface on their
# node into a gateway from the mesh to another network (usually the global Net).
class Gateways(object):
    # Path to network configuration database.
    #netconfdb = '/var/db/controlpanel/network.sqlite'
    netconfdb = '/home/drwho/network.sqlite'

    # Pretends to be index.html.
    def index(self):
        ethernet_buttons = ""
        wireless_buttons = ""

        # Open a connection to the network configuration database.
        connection = sqlite3.connect(self.netconfdb)
        cursor = connection.cursor()

        # Generate a list of Ethernet interfaces on the node that are enabled.
        # Each interface gets its own button in a table.
        cursor.execute("SELECT interface FROM wired WHERE gateway='no';")
        results = cursor.fetchall()
        if len(results):
            for interface in results:
                ethernet_buttons = ethernet_buttons + "<td><input type='submit' name='interface' value='" + interface[0] + "' /></td>\n"

        # Generate a list of wireless interfaces on the node that are not
        # enabled but are known.  As before, each button gets is own button
        # in a table.
        cursor.execute("SELECT mesh_interface FROM wireless WHERE gateway='no';")
        results = cursor.fetchall()
        if len(results):
            for interface in results:
                wireless_buttons = wireless_buttons + "<td><input type='submit' name='interface' value='" + interface[0] + "' /></td>\n"

        # Close the connection to the database.
        cursor.close()

        # Render the HTML page.
        try:
            page = templatelookup.get_template("/gateways/index.html")
            return page.render(title = "Network Gateway",
                               purpose_of_page = "Configure Network Gateway",
                               ethernet_buttons = ethernet_buttons,
                               wireless_buttons = wireless_buttons)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "\n"
                print "Error in file %s\n\tline %s\n\tfunction %s" % (filename, lineno, function)
                print "Execution died on line %s\n" % line
                print "%s: %s" % (str(traceback.error.__class__.__name__),
                    traceback.error)
    index.exposed = True

    # Implements step two of the wired gateway configuration process: turning
    # the gateway on.  This method assumes that whichever Ethernet interface
    # chosen is already configured via DHCP through ifplugd.
    def tcpip(self, interface=None):

        # Run the "Are you sure?" page through the template interpeter.
        try:
            page = templatelookup.get_template("/gateways/confirm.html")
            return page.render(title = "Enable gateway?",
                               purpose_of_page = "Confirm gateway mode.",
                               interface = interface)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "\n"
                print "Error in file %s\n\tline %s\n\tfunction %s" % (filename, lineno, function)
                print "Execution died on line %s\n" % line
                print "%s: %s" % (str(traceback.error.__class__.__name__),
                    traceback.error)
    tcpip.exposed = True


    # Method that does the deed of turning an interface into a gateway.
    def activate(self, interface=None):
        # Turn on NAT using iptables to the network interface in question.
        nat_command = ['', '', ]
        process - subprocess.Popen(nat_command)

        # Kill babeld, then re-run it using an extra configuration option to
        # announce the new route to the mesh.

        # Update the network configuration database to reflect the fact that
        # the interface is now a gateway.

        # Display the confirmation of the operation to the user.
        try:
            page = templatelookup.get_template("/gateways/done.html")
            return page.render(title = "Enable gateway?",
                               purpose_of_page = "Confirm gateway mode.",
                               interface = interface)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "\n"
                print "Error in file %s\n\tline %s\n\tfunction %s" % (filename, lineno, function)
                print "Execution died on line %s\n" % line
                print "%s: %s" % (str(traceback.error.__class__.__name__),
                    traceback.error)
    activate.exposed = True

    # Allows the user to enter the ESSID and wireless channel of the node's
    # wireless network gateway.  Takes as an argument the value of the
    # 'interface' variable defined in the form on /network/index.html.
    def wireless(self, interface=None):
        # Store the name of the network interface chosen by the user in the
        # object's attribute set and then generate the name of the client
        # interface.
        self.mesh_interface = interface
        self.client_interface = interface + ':1'

        # Default settings for /network/wireless.html page.
        channel = 3
        essid = 'Byzantium'

        # This is a hidden class attribute setting, used for sanity checking
        # later in the configuration process.
        self.frequency = frequencies[channel - 1]

        # Set up the warning in case the interface is already configured.
        warning = ''

        # If a network interface is marked as configured in the database, pull
        # its settings and insert them into the page rather than displaying the
        # defaults.
        connection = sqlite3.connect(self.netconfdb)
        cursor = connection.cursor()
        template = (interface, )
        cursor.execute("SELECT enabled, channel, essid FROM wireless WHERE mesh_interface=?;", template)
        result = cursor.fetchall()
        if result and (result[0][0] == 'yes'):
            channel = result[0][1]
            essid = result[0][2]
            warning = '<p>WARNING: This interface is already configured!  Changing it now will break the local mesh!  You can hit cancel now without changing anything!</p>'
        connection.close()
        
        # The forms in the HTML template do everything here, as well.  This
        # method only accepts input for use later.
        try:
            page = templatelookup.get_template("/network/wireless.html")
            return page.render(title = "Configure wireless for Byzantium node.",
                           purpose_of_page = "Set wireless network parameters.",
                           warning = warning, interface = self.mesh_interface,
                           channel = channel, essid = essid)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "\n"
                print "Error in file %s\n\tline %s\n\tfunction %s" % (filename, lineno, function)
                print "Execution died on line %s\n" % line
                print "%s: %s" % (str(traceback.error.__class__.__name__),
                    traceback.error)
    wireless.exposed = True

    # Configure the network interface.
    def set_ip(self):
        # If we've made it this far, the user's decided to (re)configure a
        # network interface.  Full steam ahead, damn the torpedoes!

        # First, take the wireless NIC offline so its mode can be changed.
        command = '/sbin/ifconfig ' + self.mesh_interface + ' down'
        output = os.popen(command)
        time.sleep(5)

        # Wrap this whole process in a loop to ensure that stubborn wireless
        # interfaces are configured reliably.  The wireless NIC has to make it
        # all the way through one iteration of the loop without errors before
        # we can go on.
        while True:
            # Set the mode, ESSID and channel.
            command = '/sbin/iwconfig ' + self.mesh_interface + ' mode ad-hoc'
            output = os.popen(command)
            command = '/sbin/iwconfig ' + self.mesh_interface + ' essid ' + self.essid
            output = os.popen(command)
            command = '/sbin/iwconfig ' + self.mesh_interface + ' channel ' + self.channel
            output = os.popen(command)

            # Run iwconfig again and capture the current wireless configuration.
            command = '/sbin/iwconfig ' + self.mesh_interface
            output = os.popen(command)
            configuration = output.readlines()

            # Test the interface by going through the captured text to see if
            # it's in ad-hoc mode.  If it's not, put it in ad-hoc mode and go
            # back to the top of the loop to try again.
            for line in configuration:
                if 'Mode' in line:
                    line = line.strip()
                    mode = line.split(' ')[0].split(':')[1]
                    if mode != 'Ad-Hoc':
                        continue

            # Test the ESSID to see if it's been set properly.
            for line in configuration:
                if 'ESSID' in line:
                    line = line.strip()
                    essid = line.split(' ')[-1].split(':')[1]
                    if essid != self.essid:
                        continue

            # Check the wireless channel to see if it's been set properly.
            for line in configuration:
                if 'Frequency' in line:
                    line = line.strip()
                    frequency = line.split(' ')[2].split(':')[1]
                    if frequency != self.frequency:
                        continue

            # "Victory is mine!"
            # --Stewie, _Family Guy_
            break

        # Call ifconfig and set up the network configuration information.
        command = '/sbin/ifconfig ' + self.mesh_interface + ' ' + self.mesh_ip
        command = command + ' netmask ' + self.mesh_netmask + ' up'
        output = os.popen(command)
        time.sleep(5)

        # Add the client interface.
        command = '/sbin/ifconfig ' + self.client_interface + ' ' + self.client_ip + ' up'
        output = os.popen(command)

        # Commit the interface's configuration to the database.
        connection = sqlite3.connect(self.netconfdb)
        cursor = connection.cursor()

        # Update the wireless table.
        template = ('yes', self.channel, self.essid, self.mesh_interface, self.client_interface, self.mesh_interface, )
        cursor.execute("UPDATE wireless SET enabled=?, channel=?, essid=?, mesh_interface=?, client_interface=? WHERE mesh_interface=?;", template)
        connection.commit()
        cursor.close()

        # Send this information to the methods that write the /etc/hosts and
        # dnsmasq config files.
        self.make_hosts(self.client_ip)
        self.configure_dnsmasq(self.client_ip)

        # Render and display the page.
        try:
            page = templatelookup.get_template("/network/done.html")
            return page.render(title = "Network interface configured.",
                               purpose_of_page = "Configured!",
                               interface = self.mesh_interface,
                               ip_address = self.mesh_ip,
                               netmask = self.mesh_netmask,
                               client_ip = self.client_ip,
                               client_netmask = self.client_netmask)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "\n"
                print "Error in file %s\n\tline %s\n\tfunction %s" % (filename, lineno, function)
                print "Execution died on line %s\n" % line
                print "%s: %s" % (str(traceback.error.__class__.__name__),
                    traceback.error)
    set_ip.exposed = True

    # Method that generates an /etc/hosts.mesh file for the node for dnsmasq.
    # Takes three args, the first and last IP address of the netblock.  Returns
    # nothing.
    def make_hosts(self, starting_ip=None):
        # See if the /etc/hosts.mesh backup file exists.  If it does, delete it.
        old_hosts_file = self.hosts_file + '.bak'
        if os.path.exists(old_hosts_file):
            os.remove(old_hosts_file)

        # Back up the old hosts.mesh file.
        if os.path.exists(self.hosts_file):
            os.rename(self.hosts_file, old_hosts_file)

        # We can make a few assumptions given only the starting IP address of
        # the client IP block.  Each node only has a /24 netblock for clients,
        # so we only have to generate 254 entries for that file (.2-254).
        # First, split the last octet off of the IP address passed to this
        # method.
        (octet_one, octet_two, octet_three, octet_four) = starting_ip.split('.')
        prefix = octet_one + '.' + octet_two + '.' + octet_three + '.'

        # Generate the contents of the new hosts.mesh file.
        hosts = open(self.hosts_file, "w")
        line = prefix + str('1') + '\tbyzantium.byzantium.mesh\n'
        hosts.write(line)
        for i in range(2, 255):
            line = prefix + str(i) + '\tclient-' + prefix + str(i) + '.byzantium.mesh\n'
            hosts.write(line)
        hosts.close()

        # Test for successful generation.
        if not os.path.exists(self.hosts_file):
            # Set an error message and put the old file back.
            # MOOF MOOF MOOF - Error message goes here.
            os.rename(old_hosts_file, self.hosts_file)
        return

    # Generates an /etc/dnsmasq.conf.include file for the node.  Takes two
    # args, the starting IP address.
    def configure_dnsmasq(self, starting_ip=None):
        # First, split the last octet off of the IP address passed into this
        # method.
        (octet_one, octet_two, octet_three, octet_four) = starting_ip.split('.')
        prefix = octet_one + '.' + octet_two + '.' + octet_three + '.'
        start = prefix + str('2')
        end = prefix + str('254')

        # Use that to generate the line for the config file.
        # dhcp-range=<starting IP>,<ending IP>,<length of lease>
        directive = 'dhcp-range=' + start + ',' + end + ',5m\n'

        # If an include file already exists, move it out of the way.
        oldfile = self.dnsmasq_include_file + '.bak'
        if os.path.exists(oldfile):
            os.remove(oldfile)

        # Back up the old dnsmasq.conf.include file.
        if os.path.exists(self.dnsmasq_include_file):
            os.rename(self.dnsmasq_include_file, oldfile)

        # Generate the new include file.
        file = open(self.dnsmasq_include_file, 'w')
        file.write(directive)
        file.close()

        # Restart dnsmasq.
        output = subprocess.Popen(['/etc/rc.d/rc.dnsmasq', 'restart'])
        return
