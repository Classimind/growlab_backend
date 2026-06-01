class FirmwareError(Exception):
    pass


class UploadTooLargeError(FirmwareError):
    pass


class SignatureMissingError(FirmwareError):
    pass