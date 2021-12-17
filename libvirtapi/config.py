# -*- coding: utf-8 -*-
import configparser
import os
"""
for example:
    import config as cfg
    CONF = cfg.CONF
    CONF.get("default", "verbose")
"""

# use DEFAULT_CONFIG if no configuration file
DEFAULT_CONFIG = {
    "default": {
        "log_level":  "info",
        "log_file": "/var/log/libvirtapi.log",
        "debug": "True",
        "logfile_size": "100",
        "logfile_backup_count": "5",
        "libvirt_url": "qemu+tcp://192.168.0.234/system",
        "auth_name": "libvirtapi",
        "auth_uuid": "2c47df88-2f34-49f0-a8f9-471f33116e2b",
        "available_cpu": "4",
        "libvirtapi_ip": "192.168.0.129"
    }
}


class ConfigOpts(configparser.ConfigParser):
    def __init__(self):
        configparser.DEFAULTSECT = "default"
        configparser.ConfigParser.__init__(self)

    def parse_cfg(self, _file):
        if os.path.exists(_file):
            self.read(_file)
        if not self.sections():
            print("failed to parse config file, using default value")
            for section, pair_options in DEFAULT_CONFIG.items():
                if section not in ["default"]:
                    self.add_section(section)
                for option, value in pair_options.items():
                    if not self.has_section("default"):
                        self.add_section("default")
                    self.set(section, option, value)
        else:
            for section, pair_options in DEFAULT_CONFIG.items():
                for option, value in pair_options.items():
                    if not self.has_option(section, option):
                        self.set(section, option, value)


CONF = ConfigOpts()


def config_init(config_file):
    global CONF
    CONF.parse_cfg(config_file)
