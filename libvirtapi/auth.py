# -*- coding: utf-8 -*-
from flask import g, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from libvirtapi import config as cfg

CONF = cfg.CONF

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    users = {
        CONF.get("default", "auth_name"): generate_password_hash(CONF.get("default", "auth_uuid")),
    }
    if username in users:
        return check_password_hash(users.get(username), password)
    return False
