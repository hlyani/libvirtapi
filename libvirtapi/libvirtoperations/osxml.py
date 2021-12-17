from xml.etree.ElementTree import Element


class OSXML():
    def __init__(self, conn, arch=None):
        if arch is None:
            self.arch = 'x86_64'
        self.arch = arch

    def getXML(self):
        _os = Element('os')

        _type = Element(
            'type', attrib={'arch': self.arch, 'machine': 'pc-i440fx-rhel7.0.0'})

        _type = Element(
            'type', attrib={'arch': self.arch})

        _type.text = 'hvm'

        boot1 = Element('boot', attrib={'dev': 'cdrom'})
        boot2 = Element('boot', attrib={'dev': 'hd'})

        _os.append(_type)
        _os.append(boot2)
        _os.append(boot1)

        return _os
