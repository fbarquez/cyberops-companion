"""
CTI Feed Integration Exceptions.

Custom exceptions for handling errors from threat intelligence feed integrations.
"""


class CTIFeedError(Exception):
    """Base exception for CTI feed errors."""

    def __init__(self, message: str, feed_type: str = None, details: dict = None):
        self.feed_type = feed_type
        self.details = details or {}
        super().__init__(message)


class FeedConnectionError(CTIFeedError):
    """Error connecting to the feed source."""

    pass


class FeedAPIError(CTIFeedError):
    """Error from the feed API."""

    def __init__(
        self,
        message: str,
        feed_type: str = None,
        status_code: int = None,
        response_body: str = None,
    ):
        super().__init__(message, feed_type)
        self.status_code = status_code
        self.response_body = response_body


class FeedAuthError(CTIFeedError):
    """Authentication error with the feed."""

    pass


class FeedRateLimitError(CTIFeedError):
    """Rate limit exceeded for the feed."""

    def __init__(
        self,
        message: str,
        feed_type: str = None,
        retry_after: int = None,
    ):
        super().__init__(message, feed_type)
        self.retry_after = retry_after  # Seconds until rate limit resets


class FeedParseError(CTIFeedError):
    """Error parsing data from the feed."""

    pass


class FeedConfigError(CTIFeedError):
    """Invalid feed configuration."""

    pass


class FeedTimeoutError(CTIFeedError):
    """Timeout while fetching from feed."""

    pass
