import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from libvirtapi.utils.utils import uuid_generate, random_mac
from libvirtapi.libvirtoperations.osxml import OSXML

import time


class Guest():
    def __init__(self, conn, options):
        self.conn = conn
        self.options = options

        self.setDefaultValues()

    def setDefaultValues(self):
        self.os = OSXML(self.conn, arch="x86_64")

    def guestGetXML(self, boot, image):
        # Generate the XML out of class variables
        opt = self.options

        domain = Element('domain', attrib={
            'type': 'kvm', 'xmlns:qemu': 'http://libvirt.org/schemas/domain/qemu/1.0'})
        name = Element('name')
        name.text = opt.get("name")

        uuid = Element('uuid')
        uuid.text = uuid_generate()

        description = Element('description')
        description.text = opt.get("description")

        memory = Element('memory', attrib={'unit': 'GiB'})
        memory.text = opt.get("mem")

        currentMemory = Element('currentMemory', attrib={
            'unit': 'GiB'})

        currentMemory.text = opt.get("mem")

        domain_os = self.os.getXML()

        vcpu = Element('vcpu', attrib={'placement': 'static'})
        vcpu.text = self.options.get("vcpu")

        features = Element('features')
        acpi = Element('acpi')
        apic = Element('apic')
        features.append(acpi)
        features.append(apic)

        cpu = Element('cpu', attrib={'mode': 'host-model', 'check': 'partial'})
        model = Element('model', attrib={'fallback': 'allow'})
        cpu.append(model)

        clock = Element('clock', attrib={'offset': 'utc'})
        timer1 = Element('timer', attrib={
            'name': 'rtc', 'tickpolicy': 'catchup'})
        timer2 = Element('timer', attrib={
            'name': 'pit', 'tickpolicy': 'delay'})
        timer3 = Element('timer', attrib={'name': 'hpet', 'present': 'no'})
        clock.append(timer1)
        clock.append(timer2)
        clock.append(timer3)

        createDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        metadata = Element('metadata', attrib={'createDate': createDate})

        on_poweroff = Element('on_poweroff')
        on_poweroff.text = 'destroy'
        on_reboot = Element('on_reboot')
        on_reboot.text = 'restart'
        on_crash = Element('on_crash')
        on_crash.text = 'destroy'

        pm = Element('pm')
        pm1 = Element('suspend-to-mem', attrib={'enabled': 'no'})
        pm2 = Element('suspend-to-disk', attrib={'enabled': 'no'})
        pm.append(pm1)
        pm.append(pm2)

        devices = self.devices(boot, image)

        cmdline = Element('qemu:commandline')
        arg = Element('qemu:arg', attrib={'value': '-coretek-rt'})
        cmdline.append(arg)

        domain.append(name)
        domain.append(uuid)
        domain.append(description)
        domain.append(metadata)
        domain.append(memory)
        domain.append(currentMemory)
        domain.append(vcpu)
        domain.append(features)
        domain.append(cpu)
        domain.append(clock)
        domain.append(on_poweroff)
        domain.append(on_reboot)
        domain.append(on_crash)
        domain.append(pm)
        domain.append(domain_os)
        domain.append(devices)
        domain.append(cmdline)

        return (ET.tostring(domain))

    def devices(self, boot, image=''):
        text = """
        <devices>
            <emulator>/usr/bin/qemu-system-x86_64</emulator>
            <disk device="disk" type="file">
                <driver name="qemu" type="qcow2" />
                <source file="%s" />
                <target bus="ide" dev="hda" />
                <address bus="0" controller="0" target="0" type="drive" unit="0" />
            </disk>
            <disk device="cdrom" type="file">
                <driver name="qemu" type="raw" />
                <source file="%s" />
                <target bus="ide" dev="hdb" />
                <readonly />
                <address bus="0" controller="0" target="0" type="drive" unit="1" />
            </disk>
            <controller index="0" model="ich9-ehci1" type="usb">
                <address bus="0x00" domain="0x0000" function="0x7" slot="0x06" type="pci" />
            </controller>
            <controller index="0" model="ich9-uhci1" type="usb">
                <master startport="0" />
                <address bus="0x00" domain="0x0000" function="0x0" multifunction="on" slot="0x06" type="pci" />
            </controller>
            <controller index="0" model="ich9-uhci2" type="usb">
                <master startport="2" />
                <address bus="0x00" domain="0x0000" function="0x1" slot="0x06" type="pci" />
            </controller>
            <controller index="0" model="ich9-uhci3" type="usb">
                <master startport="4" />
                <address bus="0x00" domain="0x0000" function="0x2" slot="0x06" type="pci" />
            </controller>
            <controller index="0" model="pci-root" type="pci" />
            <controller index="0" type="ide">
                <address bus="0x00" domain="0x0000" function="0x1" slot="0x01" type="pci" />
            </controller>
            <controller index="0" type="virtio-serial">
                <address bus="0x00" domain="0x0000" function="0x0" slot="0x05" type="pci" />
            </controller>
            <interface type='bridge'>
                <mac address='%s'/>
                <source bridge='br0'/>
                <model type='virtio'/>
                <address bus="0x00" domain="0x0000" function="0x0" slot="0x03" type="pci" />
            </interface>
            <serial type='pty'>
                <target type='isa-serial' port='0'>
                    <model name='isa-serial'/>
                </target>
            </serial>
            <console type='pty'>
                <target type='serial' port='0'/>
            </console>
            <channel type='unix'>
                <target type='virtio' name='org.qemu.guest_agent.0'/>
                <address type='virtio-serial' controller='0' bus='0' port='1'/>
            </channel>
            <channel type='spicevmc'>
            <target type='virtio' name='com.redhat.spice.0'/>
                <address type='virtio-serial' controller='0' bus='0' port='2'/>
            </channel>
            <input type='tablet' bus='usb'>
                <address type='usb' bus='0' port='1'/>
            </input>
            <input type='mouse' bus='ps2'/>
            <input type='keyboard' bus='ps2'/>
            <graphics type='vnc' port='-1' autoport='yes' keymap='en-us' listen='0.0.0.0'>
                <listen type='address'/>
            </graphics>
            <sound model="ich6">
                <address bus="0x00" domain="0x0000" function="0x0" slot="0x04" type="pci" />
            </sound>
            <video>
                <model heads="1" ram="65536" type="qxl" vgamem="16384" vram="65536" />
                <address bus="0x00" domain="0x0000" function="0x0" slot="0x02" type="pci" />
            </video>
            <redirdev bus="usb" type="spicevmc"></redirdev>
            <redirdev bus="usb" type="spicevmc"></redirdev>
            <memballoon model="virtio">
                <address bus="0x00" domain="0x0000" function="0x0" slot="0x07" type="pci" />
            </memballoon>
        </devices>
        """ % (boot, image, random_mac())

        return ET.XML(text)
