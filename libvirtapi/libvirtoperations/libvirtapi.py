# -*- coding: utf-8 -*-
import logging
import math
import time

try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    HAS_LIBVIRT = False

from libvirtapi import config as cfg
from libvirt import libvirtError
from xml.dom import minidom
from salt._compat import StringIO as _StringIO
from salt.exceptions import CommandExecutionError
from libvirtapi.libvirtoperations.guest import Guest
from libvirtapi.utils.utils import xml_to_dict
from libvirtapi.utils.utils import uuid_generate as genuuid

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

"""
defualt stauts map
{
    0: "NoState",
    1: "Running",
    2: "Blocked",
    3: "Paused",
    4: "Shutdown",
    5: "Shutoff",
    6: "Crashed",
    7: "PMSuspended"
}
"""

VIRT_STATE_NAME_MAP = {0: "NoState",
                       1: "Running",
                       2: "Blocked",
                       3: "Paused",
                       4: "Stopping",
                       5: "Stopped",
                       6: "Crashed",
                       7: "PMSuspended"}


class LibvirtConnect:
    connect = None

    def __new__(cls, *args, **kwargs):
        """
        连接不存在时，创建
        连接不可用时，创建
        """
        if not cls.connect:
            cls.connect = cls._libvirt_connect()
            return cls.connect

        try:
            """
            该方法会在 flask 窗口上打印 libvirt: Domain Config error : invalid connection pointer in virConnectIsAlive。
            除此之外一切正常，目前未找到解决办法。
            TODO: libvirt: Domain Config error，该错误不会被Exception捕获，似乎只是输出信息。当前不影响正常功能。
            """
            is_alive = cls.connect.isAlive()
            if not is_alive:
                cls.connect = None
                cls.connect = cls._libvirt_connect()

        except libvirtError:
            """
            由于 isAlive 方法会抛异常，这是不合理的，但是没有办法。
            进入该步骤，证明连接不可用。
            再次进行连接，如果异常，则向上层传递。
            """
            cls.connect = None
            cls.connect = cls._libvirt_connect()
        return cls.connect

    def _libvirt_connect():
        libvirt_url = CONF.get("default", "libvirt_url")
        return libvirt.open(libvirt_url)


class LibvirtBase:
    def __init__(self):
        self.conn = LibvirtConnect()


class LibvirtManager(LibvirtBase):
    def _virtual(self):
        if not HAS_LIBVIRT:
            return False
        return "virt"

    def _get_dom(self, vm_name):
        return self.conn.lookupByName(vm_name)

    def get_xml(self, vm_name):
        dom = self._get_dom(vm_name)
        return dom.XMLDesc(0)

    def get_volume_xml(self, volume_name, pool_name="default"):
        dom = self.get_pool(pool_name).storageVolLookupByName(volume_name)
        return dom.XMLDesc(0)

    def get_disks(self, vm_name):
        disks = []
        domain = xml_to_dict(self.get_xml(vm_name)).get("domain")
        disks_dom = domain.get("devices").get("disk")
        for disk in disks_dom:
            if not isinstance(disk, dict) or disk.get("device") != "disk":
                continue
            tmp = {"name": disk.get("source").get(
                "file").split("/")[5], "file": disk.get("source").get(
                "file"), "dev": disk.get("target").get("dev")}
            disks.append(tmp)
        return disks

    def get_vnc(self, vm_name):
        out = {"autoport": "",
               "keymap": "",
               "listen": "",
               "port": "",
               "url": "",
               "type": "vnc"}
        xml = self.get_xml(vm_name)
        ssock = _StringIO(xml)
        doc = minidom.parse(ssock)
        for node in doc.getElementsByTagName("domain"):
            g_nodes = node.getElementsByTagName("graphics")
            for g_node in g_nodes:
                for key in g_node.attributes.keys():
                    out[key] = g_node.getAttribute(key)

        out["listen"] = self.get_host_info().get("host_ip")
        out["url"] = "http://%s:6080/vnc_lite.html?path=websockify?token=%s" % (
            CONF.get("default", "libvirtapi_ip"), vm_name)

        return out

    def get_vm_info(self, vm_name):
        try:
            domain = xml_to_dict(self.get_xml(vm_name)).get("domain")
            dom = self._get_dom(vm_name)
            raw = dom.info()
            return {
                "platform": "Linux",  # 虚拟机平台信息
                "host": self.get_host_info(),
                "autostart": "yes" if dom.autostart() else "no",
                "console": self.get_vnc(vm_name),
                "cpu": raw[3],
                "description": domain.get("description"),
                "createDate": domain.get("metadata").get("createDate"),
                "disks": self.get_disks(vm_name),
                "id": dom.ID(),
                "mem": int(raw[2]) * 1024,  # 默认是KiB,返回Byte
                "name": vm_name,
                "state": VIRT_STATE_NAME_MAP.get(raw[0], "Unknown"),
                "type": "rt",
                "uuid": dom.UUIDString()}
        except:
            return {}

    def _list_active_vms(self):
        vms = []
        for id in self.conn.listDomainsID():
            vms.append(self.conn.lookupByID(id))
        return vms

    def _list_inactive_vms(self):
        vms = []
        for vm_name in self.conn.listDefinedDomains():
            vms.append(self.conn.lookupByName(vm_name))
        return vms

    def list_vms(self):
        vm_objects = []
        vm_objects.extend(self._list_active_vms())
        vm_objects.extend(self._list_inactive_vms())
        vms = []
        for obj in vm_objects:
            vms.append(self.get_vm_info(obj.name()))

        # 将 vnc token 写入 novnc 配置文件
        with open(r"novnc-token.conf", "w") as f:
            f.writelines(["%s: %s:%s%s" % (vm["name"], vm["console"]["listen"],
                                           vm["console"]["port"], "\n") for vm in vms if vm["console"]["port"] != "-1"])

        return vms

    def get_vm_binding_cpus(self, vmname):
        cpuset = []
        doc = minidom.parse(_StringIO(self.get_xml(vmname)))
        for node in doc.getElementsByTagName("cputune"):
            i_nodes = node.getElementsByTagName("vcpupin")
            for i_node in i_nodes:
                cpuset.append(i_node.getAttribute("cpuset"))
        return cpuset

    def list_storage_pools(self):
        return self.conn.listStoragePools()

    # reserve function
    def create_default_pool(self):
        if not self.conn.listAllStoragePools():
            xml_content = """
            <pool type="dir">
                <name>default</name>
                <target>
                    <path>/var/lib/libvirt/images</path>
                </target>
                <permissions>
                    <mode>0755</mode>
                    <owner>-1</owner>
                    <group>-1</group>
                </permissions>
            </pool>
            """
            pool = self.conn.storagePoolDefineXML(xml_content, 0)
            pool.setAutostart(1)
            if not pool.isActive():
                raise Exception(
                    "please restart libvirtd: 'systemctl restart libvirtd' or 'virsh pool-start default'")
        return self.get_pool()

    def get_pool(self, pool_name="default"):
        try:
            return self.conn.storagePoolLookupByName(pool_name)
        except libvirtError as e:
            LOG.debug(e)
            return None

    def generate_volume_xml(self, volume_name, default_pool_path, volume_size):
        if not default_pool_path:
            default_pool_path = "/var/lib/libvirt/images"
        return """
        <volume>
            <name>""" + volume_name + """</name>
            <allocation>0</allocation>
            <capacity unit="GiB">""" + volume_size + """</capacity>
            <target>
                <path>""" + default_pool_path + """/""" + volume_name + """</path>
                <format type='""" + volume_name.split('.')[-1] + """'/>
                <permissions>
                    <owner>107</owner>
                    <group>107</group>
                    <mode>0744</mode>
                    <label>virt_image_t</label>
                </permissions>
            </target>
        </volume>
        """

    def create_volume(self, volume_name, default_pool_path, volume_size):
        volume_xml = self.generate_volume_xml(
            volume_name, default_pool_path, volume_size)

        if not self.volume_info(volume_name):
            self.get_pool().createXML(volume_xml, 0)
            return self.volume_info(volume_name)
        else:
            return {}

    def clone_volume(self, volume_name, default_pool_path, volume_size, image):
        volume_xml = self.generate_volume_xml(
            volume_name, default_pool_path, volume_size)

        if not self.volume_info(volume_name):
            self.get_pool().createXMLFrom(volume_xml, image, 0)
            return self.volume_info(volume_name)
        else:
            return {}

    def list_volumes(self, pool_name="default"):
        pool = self.get_pool(pool_name)
        vols = [self.volume_info(vol, pool_name)
                for vol in pool.listVolumes()]
        return vols

    def list_images(self):
        # 镜像默认路径 /var/lib/libvirt/mirrors
        images = [vol for vol in self.list_volumes("images")]
        return images

    def volume_info(self, volume_name, pool_name="default"):
        volume = self.get_volume(volume_name, pool_name)
        if not volume:
            return volume
        volume_info = volume.info()
        path = volume.path()
        vol = {
            "name": volume_name,
            "path": path,
            "capacity": volume_info[1],
            "allocation": volume_info[2],
            "type": volume_name.split(".")[-1]
        }
        return vol

    def delete_volume(self, volume_name):
        volume = self.get_volume(volume_name)
        # 物理删除
        volume.wipe(0)
        # 从pool中逻辑删除
        return volume.delete(0) == 0

    def get_volume(self, volume_name, pool_name="default"):
        try:
            return self.get_pool(pool_name).storageVolLookupByName(volume_name)
        except libvirtError as e:
            LOG.debug(e)
            return None

    def resize_volume(self, volume_name, new_size):
        volume = self.get_volume(volume_name)
        path = volume.path()
        vm_name = ""
        for vm in self.list_vms():
            vm_disk = self.get_disks(vm.get("name"))
            for key in vm_disk.keys():
                if vm_disk[key] == path:
                    vm_name = vm.get("name")
        if vm_name:
            state = self.get_vm_state(vm_name)
            if state != "shutdown":
                return "The volume is in use, please uninstall or shutdown and try again"
        return volume.resize(new_size) == 0

    def get_vm_state(self, vm_name):
        state = ""
        dom = self._get_dom(vm_name)
        raw = dom.info()
        state = VIRT_STATE_NAME_MAP.get(raw[0], "Unknown")
        return state

    def create_vm(self, args):
        """
        args = {
            "name": "test",
            "vcpu": "1",
            "image": "CentOS-7-x86_64-Minimal-1708.iso",
            "mem": "2",
            "volume_size": "20"
        }

        create_vm(args)
        """

        if self.get_vm_info(args["name"]):
            raise Exception("instance %s is exist." % args["name"])

        default_pool_path = xml_to_dict(self.get_pool().XMLDesc()).get(
            "pool").get("target").get("path")

        image_info = self.volume_info(args["image"], "images")
        boot_name = args["name"] + ".qcow2"
        options = {
            "name": args["name"],
            "vcpu": args["vcpu"],
            "description": args.get("description", ""),
            "mem": args.get("mem", "1"),
            "boot": default_pool_path + "/" + boot_name
        }
        if image_info["type"] == "iso":
            self.create_volume(boot_name, default_pool_path,
                               str(args["volume_size"]))
            options["image"] = image_info["path"]
        else:
            image = self.get_volume(args["image"], "images")
            self.clone_volume(boot_name, default_pool_path,
                              str(args["volume_size"]), image)

        guest = Guest(self.conn, options)

        xml = bytes.decode(guest.guestGetXML(
            options["boot"], options.get("image", ""))).replace("\n", "")

        self.conn.createXML(xml, 0)
        self.conn.defineXML(xml)
        LOG.info("创建云主机成功：%s" % options["name"])
        return self.get_vm_info(args["name"])

    def destroy(self, vm_name):
        dom = self._get_dom(vm_name)
        return dom.destroy() == 0

    def delete(self, vm_name):
        volumes = self.get_disks(vm_name)
        volume_names = [volume['name'] for volume in volumes if volume]
        if self.get_vm_state(vm_name) in ["Running", "Stopping"]:
            self.destroy(vm_name)
            try:
                self.undefine(vm_name)
                for volume_name in volume_names:
                    self.delete_volume(volume_name)
            except libvirtError as e:
                LOG.warning(e, 'clean vm volume error')
            return {"name": vm_name, "status": "Deleted"}

        self.undefine(vm_name)
        try:
            for volume_name in volume_names:
                self.delete_volume(volume_name)
        except libvirtError as e:
            LOG.warning(e, 'clean vm volume error')
        return {"name": vm_name, "status": "Deleted"}

    def create(self, vm_name):
        dom = self._get_dom(vm_name)
        return dom.create() == 0

    def start(self, vm_name):
        return self.create(vm_name)

    def reboot(self, vm_name):
        dom = self._get_dom(vm_name)
        # reboot has a few modes of operation, passing 0 in means the
        # hypervisor will pick the best method for rebooting
        return dom.reboot(0) == 0

    def hard_reboot(self, vm_name):
        self.destroy(vm_name)
        return self.start(vm_name)

    def set_auto_start(self, vm_name, state="on"):
        dom = self._get_dom(vm_name)

        if state == "on":
            return dom.setAutostart(1) == 0
        elif state == "off":
            return dom.setAutostart(0) == 0
        else:
            # return False if state is set to something other then on or off
            return False

    def shutdown(self, vm_name):
        dom = self._get_dom(vm_name)
        return dom.shutdown() == 0

    def undefine(self, vm_name):
        dom = self._get_dom(vm_name)
        return dom.undefine() == 0

    def get_total_mem(self):
        mem = self.conn.getInfo()[1]
        # 预留10%的内存分配给libvirt程序
        mem -= mem / 10
        return math.floor(mem)

    def get_free_mem(self):
        mem = self.get_total_mem()
        for vm in self.list_vms():
            dom = self._get_dom(vm.get("name"))
            if dom.ID() > 0:
                mem -= dom.info()[2] / 1024
        return math.floor(mem)

    def get_total_cpu(self):
        return int(CONF.get('default', 'available_cpu'))

    def get_free_cpu(self):
        cpus = self.get_total_cpu()
        for vm in self.list_vms():
            dom = self._get_dom(vm.get("name"))
            if dom.ID() > 0:
                cpus -= dom.info()[3]
        return cpus

    def get_resources(self):
        total_vcpus = self.get_total_cpu()
        free_vcpus = self.get_free_cpu()
        total_memory = self.get_total_mem()
        free_memory = self.get_free_mem()
        default_pool_info = self.get_pool().info()
        images_pool_info = self.get_pool('images').info()
        images_num = len(self.list_volumes('images'))
        volume_num = len(self.list_volumes())
        vms = self.list_vms()
        res = {
            "cpu": {
                "total": total_vcpus,
                "current": total_vcpus - free_vcpus,
                "available": free_vcpus,
                "usage_rate" : '%.2f' % (((total_vcpus - free_vcpus) / total_vcpus) * 100)
            },
            "memory": {
                "total": total_memory,
                "current": total_memory - free_memory,
                "available": free_memory,
                "usage_rate": '%.2f' % (((total_memory - free_memory) / total_memory) * 100)
            },
            "disk": {
                "total": round(default_pool_info[1] / 1024 / 1024),
                "current": round(default_pool_info[2] / 1024 / 1024),
                "available": round(default_pool_info[3] / 1024 / 1024),
                "created_num": volume_num,
                "root": 0,
                "data": volume_num,
                "usage_rate": '%.2f' % ((default_pool_info[2] / default_pool_info[1]) * 100)
            },
            "poolStorage": {
                "total": round(images_pool_info[1] / 1024 / 1024),
                "current": round(images_pool_info[2] / 1024 / 1024),
                "available": round(images_pool_info[3] / 1024 / 1024),
                "created_num": images_num,
                "usage_rate": '%.2f' % ((images_pool_info[2] / images_pool_info[1]) * 100)
            },
            "image": {
                "total": images_num,
                "available": images_num,
                "available_rate": 100.00
            },
            "vm": {
                "total": len(vms),
                "run": len([vm for vm in vms if vm['state'] == 'Running']),
                "stop": len([vm for vm in vms if vm['state'] != 'Running']),
            },
            "host": {
                "total": 1,
                "run": 1,
                "stop": 0,
            },
        }
        return res

    def set_vcpus(self, vm_name, vcpus, config=False):
        if self.get_vm_state(vm_name) != "shutdown":
            return False

        dom = self._get_dom(vm_name)
        flags = libvirt.VIR_DOMAIN_VCPU_MAXIMUM

        if config:
            flags = flags | libvirt.VIR_DOMAIN_AFFECT_CONFIG

        ret1 = dom.setVcpusFlags(vcpus, flags)
        ret2 = dom.setVcpusFlags(vcpus, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

        return ret1 == ret2 == 0

    def set_mem(self, vm_name, memory, config=False):
        if self.get_vm_state(vm_name) != "shutdown":
            return False

        dom = self._get_dom(vm_name)

        # libvirt has a funny bitwise system for the flags in that the flag
        # to affect the "current" setting is 0, which means that to set the
        # current setting we have to call it a second time with just 0 set
        flags = libvirt.VIR_DOMAIN_MEM_MAXIMUM
        if config:
            flags = flags | libvirt.VIR_DOMAIN_AFFECT_CONFIG

        ret1 = dom.setMemoryFlags(memory * 1024, flags)
        ret2 = dom.setMemoryFlags(
            memory * 1024, libvirt.VIR_DOMAIN_AFFECT_CURRENT)

        # return True if both calls succeeded
        return ret1 == ret2 == 0

    def get_host_info(self):
        raw = self.conn.getInfo()
        info = {"host_ip": CONF.get("default", "libvirt_url").split("/")[2],
                "cpucores": raw[6],
                "cpumhz": raw[3],
                "cpumodel": str(raw[0]),
                "cpus": raw[2],
                "cputhreads": raw[7],
                "numanodes": raw[4],
                "phymemory": raw[1] * 1024 * 1024,  # 默认是MB，转换为Byte
                "sockets": raw[5]}
        return info
