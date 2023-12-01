# chrome_for_testing.py - helpers for chrome for testing availability

import functools
import typing

import requests


_BASE_URL = 'https://googlechromelabs.github.io/chrome-for-testing/'
_CHANNELS = ('BETA', 'CANARY', 'DEV', 'STABLE')
_ENDPOINT_JSON = tuple[str, bool]
_LAST_KNOWN_STABLE_VERSION = '119.0.6045.105'


def _request(func: typing.Callable[[typing.Any], _ENDPOINT_JSON]
            ) -> str or dict:
    """
    Makes a request and processes the response.

    :param func: function that returns endpoint and flag about expected
        type of return (json or str)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        endpoint, return_json = func(*args, **kwargs)
        r = requests.get(f'{_BASE_URL}{endpoint}')
        r.raise_for_status()
        if return_json:
            return r.json()
        return r.text
    return wrapper


@_request
def known_good_versions_json(with_download_url: bool) -> _ENDPOINT_JSON:
    """
    The version for which all CfT assets are available for download.

    :param with_download_url: if True, add an "download" property for
        each version, listing the full download URLs per asset.
    """
    endpoints = {False: 'known-good-versions.json',
                True: 'known-good-versions-with-downloads.json'}
    return endpoints[with_download_url], True


@_request
def last_known_good_versions_json(with_download_url: bool) -> _ENDPOINT_JSON:
    """
    The latest versions for which all CfT assets are available for
    download.

    :param with_download_url: if True, add an "download" property for
        each channel, listing the full download URLs per asset.
    """
    endpoints = {False: 'last-known-good-versions.json',
                 True: 'last-known-good-versions-with-downloads.json'}
    return endpoints[with_download_url], True


@_request
def latest_patch_versions_per_build_json(with_download_url: bool
                                        ) -> _ENDPOINT_JSON:
    """
    The latest versions for which all CfT assets are available for
    download, for each known combination of MAJOR.MINOR.BUILD versions.

    :param with_download_url: if True, add an "download" property for
        each version, listing the full download URLs per asset.
    """
    endpoints = {False: 'latest-patch-versions-per-build.json',
                 True: 'latest-patch-versions-per-build-with-downloads.json'}
    return endpoints[with_download_url], True


@_request
def latest_release_channel(channel: str) -> _ENDPOINT_JSON:
    """
    The latest available version at channel.

    :param channel: channel's description.
    """
    channel_ = channel.strip().upper()
    if channel_ not in _CHANNELS:
        raise ValueError(f'unrecognized channel "{channel}"')
    return f'LATEST_RELEASE_{channel_}', False


@_request
def latest_release_range(version_range: str) -> _ENDPOINT_JSON:
    """
    The latest available version within the range.

    :param version_range: description of version range.
    """
    return f'LATEST_RELEASE_{version_range.strip().upper()}', False


@_request
def latest_versions_per_milestone_json(with_download_url: bool
                                      ) -> _ENDPOINT_JSON:
    """
    The latest versions for which all CfT assets are available for
    download, for each Chrome milestone.

    :param with_download_url: if True, add an "download" property for
        each milestone, listing the full download URLs per asset.
    """
    endpoints = {False: 'latest-versions-per-milestone.json',
                 True: 'latest-versions-per-milestone-with-downloads.json'}
    return endpoints[with_download_url], True


class OutOfDateCfTVersionError(Exception):
    """Exception class for out of date version of Chrome for Testing."""

    def __init__(self, channel: str, version: str, latest_version: str):
        super().__init__(f'"{version}" is out of date. "{latest_version}" is'
                         ' the latest version available of Chrome for Testing'
                         f' at channel "{channel}".')


def raise_for_outofdate(version: str, channel: str) -> None:
    """Raises OutOfDateCfTVersionError if the version is not the latest
    version available at channel."""
    version = version.strip()
    latest_version = latest_release_channel(channel.strip()).strip()
    if version != latest_version:
        raise OutOfDateCfTVersionError(channel, version, latest_version)


def raise_for_lks_outofdate() -> None:
    """Raises OutOfDateCfTVersionError if the last known stable version
    is not the latest version available at stable channel."""
    raise_for_outofdate(_LAST_KNOWN_STABLE_VERSION, 'stable')


if __name__ == '__main__':
    import pprint
    for c in ('BETA', 'CANARY', 'DEV', 'STABLE'):
        print(f'latest_release_channel "{c}":', latest_release_channel(c))
    raise_for_lks_outofdate()
