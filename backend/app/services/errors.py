class ServiceError(Exception):
    """Base class for domain errors raised by the service layer."""

    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class ValidationError(ServiceError):
    status_code = 400


class ConflictError(ServiceError):
    status_code = 400


class AuthError(ServiceError):
    status_code = 401


class NotFoundError(ServiceError):
    status_code = 404
