"""Scanner-specific exceptions."""


class ScannerError(Exception):
    """Base exception for scanner operations."""

    def __init__(self, message: str, scanner_type: str = None):
        self.message = message
        self.scanner_type = scanner_type
        super().__init__(self.message)


class ScannerConnectionError(ScannerError):
    """Raised when connection to scanner fails."""

    pass


class ScannerAuthenticationError(ScannerError):
    """Raised when authentication to scanner fails."""

    pass


class ScannerAPIError(ScannerError):
    """Raised when scanner API returns an error."""

    def __init__(
        self, message: str, scanner_type: str = None, status_code: int = None
    ):
        super().__init__(message, scanner_type)
        self.status_code = status_code


class ScannerTimeoutError(ScannerError):
    """Raised when scanner operation times out."""

    pass


class ScannerConfigurationError(ScannerError):
    """Raised when scanner configuration is invalid."""

    pass


class ScanNotFoundError(ScannerError):
    """Raised when a scan is not found in the scanner."""

    def __init__(self, message: str, scanner_type: str = None, scan_id: str = None):
        super().__init__(message, scanner_type)
        self.scan_id = scan_id
