# -*- coding: utf-8 -*-

import logging
from flask import Blueprint, jsonify

from libvirtapi.utils.utils import get_body_json, error_handler
from libvirtapi.libvirtoperations.libvirtapi import LibvirtManager

from libvirtapi.blueprints.baseview import BaseView


bp = Blueprint("vm", __name__)
LOG = logging.getLogger(__name__)


class ListVMs(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self):
        """
        @api {get} /libvirtapi/vm 请求虚拟机列表
        @apiName listvms
        @apiGroup vm
        @apiSuccess {object} vm
        @apiExample 请求虚拟机列表
        GET /libvirtapi/vm
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        [
            {
                "autostart": "no",
                "console": {
                    "autoport": "yes",
                    "keymap": "None",
                    "listen": "127.0.0.1",
                    "port": "5904",
                    "type": "vnc"
                },
                "cpu": 10,
                "disks": {
                    "vda": "/var/lib/libvirt/images/hl-node1.qcow2"
                },
                "id": 18,
                "maxMem": 37748736,
                "mem": 37748736,
                "name": "hl-node1",
                "state": "running",
                "uuid": "0c1b9ccb-720a-440c-91bb-5489c1cb060e"
            }
            ...
        ]
        """
        try:
            lib = LibvirtManager()
            vms = lib.list_vms()
            return jsonify(vms), 200
        except Exception as e:
            return error_handler(e, "list vms error")


class VMXML(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self, name):
        """
        @api {get} /libvirtapi/vm/:name/xml 请求虚拟机xml
        @apiName xml
        @apiGroup vm
        @apiSuccess {object} vm
        @apiExample 请求虚拟机信息
        GET /libvirtapi/vm/test/xml
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        """
        try:
            lib = LibvirtManager()
            vm = lib.get_xml(name)
            return vm, 200
        except Exception as e:
            return error_handler(e, "get vm_xml info failed")


class VM(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self, name=None):
        """
        @api {get} /libvirtapi/vm/:name 请求虚拟机信息
        @apiName vm
        @apiGroup vm
        @apiSuccess {object} vm
        @apiExample 请求虚拟机信息
        GET /libvirtapi/vm/test
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        {
            "autostart": "no",
            "console": {
                "autoport": "None",
                "keymap": "None",
                "listen": "None",
                "port": "None",
                "type": "vnc"
            },
            "cpu": 1,
            "disks": {
                "hda": "/var/lib/libvirt/images/test5.qcow2",
                "hdb": "/var/lib/libvirt/images/CentOS-7-x86_64-Minimal-1708.iso"
            },
            "id": 39,
            "maxMem": 2097152,
            "mem": 2097152,
            "name": "test5",
            "state": "running",
            "uuid": "2c66f0c2-ea6e-4764-b974-7481bdb58d85"
        }
        """
        try:
            lib = LibvirtManager()
            vm = lib.get_vm_info(name)
            if not vm:
                return jsonify({"error": "not found vm info"}), 400
            return jsonify(vm), 200
        except Exception as e:
            return error_handler(e, "get vm info failed")

    # TODO: 后续开启认证
    # @auth.login_required
    def post(self):
        """
        @api {post} /libvirtapi/vm 创建虚拟机
        @apiName vm
        @apiGroup vm
        @apiSuccess {object} vm
        @apiExample 创建虚拟机
        POST /libvirtapi/vm
        Content-Type: application/json
        body:
        {
            "name": "test",
            "vcpu": "1",
            "image": "/var/lib/libvirt/images/CentOS-7-x86_64-Minimal-1708.iso",
            "mem": "2",
            "volume_size": "20"
        }

        @apiSuccessExample 成功响应: 创建的主机详细信息
        HTTP/1.1 200 OK
        {
            ...
        }
        """
        try:
            body = get_body_json()

            name = body.get("name")
            if not name:
                return jsonify({"error": "not found param name"}), 400

            vcpu = body.get("vcpu")
            if not vcpu:
                return jsonify({"error": "not found param vcpu"}), 400

            image = body.get("image")
            if not image:
                return jsonify({"error": "not found param image"}), 400

            mem = body.get("mem")
            if not mem:
                return jsonify({"error": "not found param mem"}), 400

            volume_size = body.get("volume_size")
            if not volume_size:
                return jsonify({"error": "not found param volume_size"}), 400

            lib = LibvirtManager()
            if float(mem) * 1024 > float(lib.get_free_mem()):
                return jsonify({"error": "可用内存不足，平台总可用内存 %s MB，当前可用 %s MB" %
                                         (lib.get_total_mem(), lib.get_free_mem())}), 400

            if int(vcpu) > int(lib.get_free_cpu()):
                return jsonify({"error": "可用CPU不足，实时CPU总数 %s ，当前可用 %s " %
                                         (lib.get_total_cpu(), lib.get_free_cpu())}), 400

            vm = lib.create_vm(body)
            return jsonify(vm), 200
        except Exception as e:
            return error_handler(e, "create vm info failed")

    # TODO: 后续开启认证
    # @auth.login_required
    def delete(self, name=None):
        """
        @api {post} /libvirtapi/vm 删除虚拟机
        @apiName vm
        @apiGroup vm
        @apiSuccess {object} vm
        @apiExample 删除虚拟机
        DELETE /libvirtapi/test
        Content-Type: application/json

        @apiSuccessExample 成功响应: 删除虚拟机成功
        HTTP/1.1 200 OK
        {}
        """
        try:
            if not name:
                return jsonify({"error": "not found param name"}), 400

            lib = LibvirtManager()
            ret = lib.delete(name)
            return jsonify(ret), 200
        except Exception as e:
            return error_handler(e, "delete vm info failed")


class VMAction(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def post(self, name=None):
        """
        @api {post} /libvirtapi/vm/:name/action 虚拟机操作
        @apiName vm_action
        @apiGroup vm
        @apiSuccess {string} msg
        @apiExample 虚拟机操作
        POST /libvirtapi/vm/test/action
        Content-Type: application/json
        {
            "action" : action (start, shutdown, reboot, destroy)
        }
        @apiSuccessExample 成功响应:
        HTTP/1.1 202 OK
        {}
        """
        try:
            START = "start"
            REBOOT = "reboot"
            SHUTDOWN = "shutdown"
            DESTROY = "destroy"

            if not name:
                return jsonify({"error": "not found param name"}), 400

            body = get_body_json()
            action = body.get("action")

            if not action:
                return jsonify({"error": "not found param action"}), 400

            lib = LibvirtManager()

            if action == START:
                LOG.info("%s vm: %s" % (action, name))
                lib.start(name)
            elif action == REBOOT:
                LOG.info("%s vm: %s" % (action, name))
                # FIXME: soft reboot
                # lib.reboot(name)
                lib.hard_reboot(name)
            elif action == DESTROY:
                LOG.info("%s vm: %s" % (action, name))
                lib.destroy(name)
            elif action == SHUTDOWN:
                LOG.info("%s vm: %s" % (action, name))
                lib.shutdown(name)
            else:
                return jsonify({"error": "incorrect action"}), 400

            return jsonify({"name": name}), 202
        except Exception as e:
            return error_handler(e, "opertate vm failed")


bp.add_url_rule('/libvirtapi/vm', view_func=ListVMs.as_view("list_vms"))
bp.add_url_rule('/libvirtapi/vm/<string:name>', view_func=VM.as_view("vm"))
bp.add_url_rule('/libvirtapi/vm/<string:name>/xml',
                view_func=VMXML.as_view("get_vm_xml"))
bp.add_url_rule('/libvirtapi/vm', view_func=VM.as_view("create_vm"))
bp.add_url_rule('/libvirtapi/vm/<string:name>/action',
                view_func=VMAction.as_view('vm_action'))
