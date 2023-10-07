class ScreenshotError(Exception):
    ...


class ScreenshotResponseError(ScreenshotError):
    ...


class ScreenshotRequestError(ScreenshotError):
    ...


class ScreenshotPermissionError(ScreenshotError):
    ...


class ScreenshotTimeoutError(ScreenshotError):
    ...
