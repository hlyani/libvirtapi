# -*- coding: utf-8 -*-
import os
import logging

from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_cors import CORS
import eventlet
from eventlet import wsgi
from libvirtapi import config as cfg

from libvirtapi.blueprints.libvirtapi.vm.views import bp as vm_bp
from libvirtapi.blueprints.libvirtapi.volume.views import bp as volume_bp
from libvirtapi.blueprints.libvirtapi.image.views import bp as image_bp
from libvirtapi.blueprints.libvirtapi.monitor.views import bp as monitor_bp

CONF = cfg.CONF
FILE_FORMAT = ("[%(asctime)s.%(msecs)03d][%(pathname)s:%(funcName)s]"
               "[%(levelname)s] %(message)s")
LOG = logging.getLogger(__name__)


def create_app(simple_context=False):
    app = Flask("libvirtapi")

    configure_app(app)
    app.register_blueprint(vm_bp)
    app.register_blueprint(volume_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(monitor_bp)
    if not simple_context:
        CORS(app)

    return app


def log_init(app):
    root = logging.getLogger()
    level = CONF.get("default", "log_level").upper()
    root.setLevel(level)
    log_file = CONF.get("default", "log_file")
    log_max_size = CONF.getint("default", "logfile_size") * 1024 * 1024
    log_backup_count = CONF.getint("default", "logfile_backup_count")
    fh = RotatingFileHandler(
        log_file, maxBytes=log_max_size, backupCount=log_backup_count
    )
    fh.setFormatter(
        logging.Formatter(fmt=FILE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    )
    root.addHandler(fh)
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)


def configure_app(app):
    config_file = os.getenv(
        "LIBVIRTAPI_CONFIG_FILE") or "/etc/libvirtapi/libvirtapi.conf"

    cfg.config_init(config_file)

    log_init(app)


def main():
    app = create_app()
    wsgi.server(eventlet.listen(("", 8778)), app)


if __name__ == "__main__":
    main()
