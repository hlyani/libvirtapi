# -*- coding: utf-8 -*-

import logging
from flask import Blueprint, jsonify

from libvirtapi.libvirtoperations.libvirtapi import LibvirtManager
from libvirtapi.utils.utils import error_handler

from libvirtapi.blueprints.baseview import BaseView


bp = Blueprint("image", __name__)
LOG = logging.getLogger(__name__)


class Image(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self):
        """
        @api {get} /libvirtapi/image 请求镜像列表
        @apiName image list
        @apiGroup image
        @apiSuccess {object} image
        @apiExample  请求镜像列表
        GET /libvirtapi/image/list
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        [
            {
                "allocation": 830472192,
                "capacity": 830472192,
                "name": "CentOS-7-x86_64-Minimal-1708.iso",
                "path": "/var/lib/libvirt/images/CentOS-7-x86_64-Minimal-1708.iso"
            }
        ]
        """
        try:
            lib = LibvirtManager()
            images = lib.list_images()
            return jsonify(images), 200
        except Exception as e:
            return error_handler(e, "list images error")


bp.add_url_rule('/libvirtapi/image',
                view_func=Image.as_view("list_image"))
