# -*- coding: utf-8 -*-

import logging
from flask import Blueprint, jsonify

from libvirtapi.utils.utils import get_body_json, error_handler
from libvirtapi.libvirtoperations.libvirtapi import LibvirtManager

from libvirtapi.blueprints.baseview import BaseView


bp = Blueprint("volume", __name__)
LOG = logging.getLogger(__name__)

class VolumeXML(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self, name):
        """
        @api {get} /libvirtapi/volume/:name/xml 请求磁盘xml
        @apiName xml
        @apiGroup volume
        @apiSuccess {object} volume
        @apiExample 请求磁盘xml
        GET /libvirtapi/volume/:name/xml
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        """
        try:
            lib = LibvirtManager()
            volume = lib.get_volume_xml(name)
            return volume, 200
        except Exception as e:
            return error_handler(e, "get volume_xml info failed")


class VolumeList(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self):
        """
        @api {get} /libvirtapi/volume 请求硬盘列表
        @apiName get_volumes
        @apiGroup volume
        @apiSuccess {object} volume
        @apiExample 请求硬盘列表
        GET /libvirtapi/volume
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        {
            ...
        }
        """
        try:
            lib = LibvirtManager()
            volumes = lib.list_volumes()
            return jsonify(volumes), 200
        except Exception as e:
            return error_handler(e, "get list_volumes failed")


class Volume(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self, name):
        """
        @api {get} /libvirtapi/volume/:name 请求硬盘
        @apiName get_volume
        @apiGroup volume
        @apiSuccess {object} volume
        @apiExample 请求硬盘
        GET /libvirtapi/volume/test
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        {
            ...
        }
        """
        try:
            lib = LibvirtManager()
            volume = lib.volume_info(name)
            return jsonify(volume), 200
        except Exception as e:
            return error_handler(e, "get list_volumes failed")

    # TODO: 后续开启认证
    # @auth.login_required
    def post(self):
        """
        @api {post} /libvirtapi/volume 创建硬盘
        @apiName create_volume
        @apiGroup volume
        @apiSuccess {object} volume
        @apiExample 创建硬盘
        POST /libvirtapi/volume
        Content-Type: application/json
        body:
        {
            "name": "test",
            "size": "20"
        }

        @apiSuccessExample 成功响应: 详细信息
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

            size = body.get("size")
            if not size:
                return jsonify({"error": "not found param size"}), 400

            lib = LibvirtManager()
            volume = lib.create_volume(name + ".qcow2", "", size)
            return jsonify(volume), 200
        except Exception as e:
            return error_handler(e, "create volume info failed")

    # TODO: 后续开启认证
    # @auth.login_required
    def delete(self, name):
        """
        @api {post} /libvirtapi/volume/:name 删除硬盘
        @apiName delete_volume
        @apiGroup volume
        @apiSuccess {object} volume
        @apiExample 删除硬盘
        POST /libvirtapi/volume/test
        Content-Type: application/json
        @apiSuccessExample 成功响应: 详细信息
        HTTP/1.1 200 OK
        {
            ...
        }
        """
        try:
            lib = LibvirtManager()
            result = lib.delete_volume(name + '.qcow2')
            return jsonify({'message': result}), 200
        except Exception as e:
            return error_handler(e, "delete volume info failed")


bp.add_url_rule('/libvirtapi/volume',
                view_func=VolumeList.as_view('list_volumes'))
bp.add_url_rule('/libvirtapi/volume/<string:name>',
                view_func=Volume.as_view('volume'))
bp.add_url_rule('/libvirtapi/volume',
                view_func=Volume.as_view('create_volume'))
bp.add_url_rule('/libvirtapi/volume/<string:name>/xml',
                view_func=VolumeXML.as_view('volume_xml'))
