import logging
from flask.views import MethodView
from flask import request


LOG = logging.getLogger(__name__)
http_method_funcs = frozenset(
    ["get", "post", "head", "options", "delete", "put", "trace", "patch"]
)


class BaseView(MethodView):
    def __getattribute__(self, item):
        # 记录日志
        # 认证
        if str(item).lower() in http_method_funcs:
            LOG.info("[%s]: %s: %s", request.remote_addr, request.method, request.path)
        return super().__getattribute__(item)