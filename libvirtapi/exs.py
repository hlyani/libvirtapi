# -*- coding: utf-8 -*-


class CustomException(Exception):
    def __init__(self, message, code=500):
        super().__init__(message)
        self.message = message
        self.code = code


class UserNotExistError(Exception):
    pass


class ResourceNotExistError(Exception):
    pass


class MissParamError(CustomException):
    pass
