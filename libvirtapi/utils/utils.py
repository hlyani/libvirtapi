# -*- coding: utf-8 -*-
import json
import traceback

import random
from flask import request
from libvirt import libvirtError
from flask import jsonify
import logging
import uuid
import xmltodict
import json

LOG = logging.getLogger(__name__)


def get_body_json():
    result = request.get_json()
    if result:
        try:
            result = json.loads(request.data)
        except ValueError as e:
            raise ValueError("cannot format json: %s, error: %s" %
                             (request.data, e))
    return result


def error_handler(e, error_description=""):
    """
    用于处理异常：
            常规异常，比如索引越界，值类型错误
            libvirt异常，由 libvirt 抛出的异常

    参数 e:
            一个异常对象，可以是内置异常对象，也可以是自己封装的异常对象。
    参数 error_description:
            自定义的异常提示信息，有些异常是人为抛出的，此类异常可以增加方便阅读的异常描述。
    """
    code = 500

    if isinstance(e, libvirtError):
        if e.get_error_code():
            # TODO: 优化返回码，libvirt返回有误
            code = e.get_error_code()
            code = 500

    else:
        if getattr(e, "code", None):
            code = getattr(e, "code")

    message = str(e)

    if error_description:
        message = "%s: %s" % (error_description, message)

    LOG.error("%s" % message)
    LOG.error(traceback.format_exc())
    return jsonify({"error": message}), code


def uuid_generate():
    return str(uuid.uuid4())


def xml_to_dict(xml):
    return xmltodict.parse(
        xml, attr_prefix="", cdata_key="")


def random_mac():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(map(lambda x: "%02x" % x, mac))
