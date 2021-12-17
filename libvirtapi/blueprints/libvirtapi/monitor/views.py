# -*- coding: utf-8 -*-

import logging
from flask import Blueprint, jsonify

from libvirtapi.utils.utils import get_body_json, error_handler
from libvirtapi.libvirtoperations.libvirtapi import LibvirtManager

from libvirtapi.blueprints.baseview import BaseView


bp = Blueprint("monitor", __name__)
LOG = logging.getLogger(__name__)


class Resource(BaseView):
    # TODO: 后续开启认证
    # @auth.login_required
    def get(self):
        """
        @api {get} /libvirtapi/resources 请求平台资源概览
        @apiName resources
        @apiGroup resource
        @apiSuccess {object} resource
        @apiExample 请求平台资源概览
        GET /libvirtapi/resources
        Content-Type: application/json
        @apiSuccessExample 成功响应:
        HTTP/1.1 200 OK
        [
            {
                ...
            }
            ...
        ]
        """
        try:
            lib = LibvirtManager()
            res = lib.get_resources()
            return jsonify(res), 200
        except Exception as e:
            return error_handler(e, "list resource error")


bp.add_url_rule('/libvirtapi/resources', view_func=Resource.as_view("resources"))
