class TuyaSDKException(Exception):
    """Base exception for the SDK"""


class ApiRequestException(TuyaSDKException):
    """Exception raised when the server returned an error."""

    def __init__(
        self,
        *,
        error_code: str,
        error_message: str,
    ) -> None:
        """Initialize exception."""
        super().__init__(f"network error:({error_code}) {error_message}")
        self.error_code = error_code
        self.error_message = error_message
