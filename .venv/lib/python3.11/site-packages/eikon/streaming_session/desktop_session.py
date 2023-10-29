# coding: utf-8

__all__ = ['DesktopSession']

import os

from appdirs import *
import logging
import socket
import httpx
from urllib.parse import urlparse
from .. import __version__
from ..tools import urljoin
from ..eikonError import EikonError
from .session import Session


class DesktopSession(Session):
    _LOCALHOST_URL = "http://127.0.0.1:{0}"
    _WS_STREAMING_PATH = "/api/v1/data/streaming/pricing"

    class Params(Session.Params):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    def __init__(self, app_key, on_state=None, on_event=None, **kwargs):
        super().__init__(app_key=app_key,
                         on_state=on_state,
                         on_event=on_event,
                         token=kwargs.get("token"),
                         dacs_user_name=kwargs.get('dacs_user_name'),
                         dacs_position=kwargs.get("dacs_position"),
                         dacs_application_id=kwargs.get("dacs_application_id"))
        from os import getenv

        self._port = None

        #   uuid is retrieved in CODEBOOK environment, it's used for DP-PROXY to manage multi-user mode
        self._user_uuid = getenv("REFINITIV_AAA_USER_ID")
        self._dp_proxy_app_version = getenv("DP_PROXY_APP_VERSION")

        # Identify base url
        self._dp_proxy_base_url = getenv("DP_PROXY_BASE_URL")
        if self._dp_proxy_base_url:
            self._base_url = self._dp_proxy_base_url
        else:
            self._base_url = DesktopSession._LOCALHOST_URL.format(self._port)

    def _get_base_url(self) -> str:
        return self._base_url

    def _get_handshake_url(self) -> str:
        handshake_url = urljoin(self._base_url, "/api/handshake")
        return handshake_url

    def _get_udf_url(self) -> str:
        """
        Returns the scripting proxy url.
        """
        udf_url = urljoin(self._base_url, "/api/v1/data")
        return udf_url

    def _get_http_session(self):
        """
        Returns the scripting proxy http session for requests.
        """
        return self._http_session

    def set_port_number(self, port_number, logger=None):
        """
        Set the port number to reach Eikon API proxy.
        """
        self._port = port_number
        self._base_url = self._update_port_in_url(self._base_url, port_number)
        parsed_url = urlparse(self._base_url)
        self._streaming_config.host = parsed_url.netloc + parsed_url.path + DesktopSession._WS_STREAMING_PATH

        if logger:
            logger.info(f"Update port number in Proxy base url: {self._base_url}")

        return

    def get_port_number(self):
        """
        Returns the port number
        """
        return self._port

    def is_session_logged(self):
        return self._streaming_session._ws_is_logged

    def _init_streaming_config(self):
        parsed_url = urlparse(self._base_url)
        self._streaming_config.host = parsed_url.netloc + parsed_url.path + DesktopSession._WS_STREAMING_PATH

        self._streaming_config.application_id = self._dacs_params.dacs_application_id
        self._streaming_config.position = self._dacs_params.dacs_position

        self._streaming_config.login_message = {
            "ID": "",
            "Domain": "Login",
            "Key": {
                "Name": "john doe",
                "Elements": {
                    "AppKey": self.app_key,
                    "ApplicationId": self._dacs_params.dacs_application_id,
                    "Position": self._dacs_params.dacs_position
                }
            }
        }
        # provide app_key to Eikon API Proxy through x_tr_applicationid header when starting websocket
        headers = [f"x-tr-applicationid: {self.app_key}"]

        app_version = os.getenv("DP_PROXY_APP_VERSION")
        if app_version:
            headers.append(f"app-version: {app_version}")

        self._streaming_config._headers = headers

    #######################################
    #  methods to open and close session  #
    #######################################
    def open(self):
        if self._state in [Session.State.Pending, Session.State.Open]:
            # session is already opened or is opening
            return self._state

        # call Session.open() based on open_async() => _init_streaming_config will be called later
        return super(DesktopSession, self).open()

    def close(self):
        return super(DesktopSession, self).close()

    ############################################
    #  methods to open asynchronously session  #
    ############################################
    async def open_async(self):
        def close_state(msg):
            self._state = Session.State.Closed
            self._on_event(self.session_id, Session.EventCode.SessionAuthenticationFailed, msg)
            self._on_state(self._state, "Session is closed.")

        if self._state in [Session.State.Pending, Session.State.Open]:
            # session is already opened or is opening
            return self._state

        error = None

        try:
            if self._dp_proxy_base_url:
                test_proxy_result = await self.check_proxy(self._base_url)
                if not test_proxy_result:
                    self.log(
                        logging.ERROR,
                        f"Error: no response from DP PROXY {self._base_url}.\nCheck if Eikon Desktop or Eikon API Proxy is running.")
            else:
                # Identify port number to update base url
                port_number = await self.identify_scripting_proxy_port()
                self.set_port_number(port_number)
            handshake_url = self._get_handshake_url()
            await self.handshake(handshake_url)
        except EikonError as e:
            self.log(logging.ERROR, e.message)
            error = e
        if not error:
            self.log(logging.INFO, f"Application ID: {self.app_key}")
            self._state = Session.State.Open
            self._on_state(Session.State.Open, "Session is opened.")
            self._init_streaming_config()
        else:
            # port number wasn't identified => do nothing ?
            self.log(logging.ERROR, "Port number was not identified, cannot send any request")

        not self._dp_proxy_base_url and not self._port and close_state("Eikon is not running")
        error and close_state(error.message)
        await super(DesktopSession, self).open_async()
        return self._state

    @staticmethod
    def read_firstline_in_file(filename: str, logger=None) -> str:
        try:
            f = open(filename)
            first_line = f.readline()
            f.close()
            return first_line
        except IOError as e:
            if logger:
                logger.error(f"I/O error({e.errno}): {e.strerror}")
            return ""

    async def identify_scripting_proxy_port(self) -> str:
        """
        Returns the port used by the Scripting Proxy stored in a configuration file.
        """
        import platform
        import os

        port = None
        path = []
        app_names = ["Data API Proxy", "Eikon API proxy", "Eikon Scripting Proxy"]
        for app_author in ["Refinitiv", "Thomson Reuters"]:
            if platform.system() == "Linux":
                path = path + [user_config_dir(app_name, app_author, roaming=True)
                               for app_name in app_names
                               if os.path.isdir(user_config_dir(app_name, app_author, roaming=True))]
            else:
                path = path + [user_data_dir(app_name, app_author, roaming=True)
                               for app_name in app_names
                               if os.path.isdir(user_data_dir(app_name, app_author, roaming=True))]

        if len(path):
            port_in_use_file = os.path.join(path[0], ".portInUse")

            # Test if ".portInUse" file exists
            if os.path.exists(port_in_use_file):
                # First test to read .portInUse file
                first_line: str = self.read_firstline_in_file(port_in_use_file)
                if first_line != "":
                    saved_port = first_line.strip()
                    test_proxy_url = self._update_port_in_url(self._base_url, saved_port)
                    test_proxy_result = await self.check_proxy(test_proxy_url)
                    if test_proxy_result:
                        port = saved_port
                        self.log(logging.INFO, f"Port {port} was retrieved from .portInUse file")
                    else:
                        self.log(logging.INFO, f"Retrieved port {saved_port} value from .portIntUse isn't valid.")

        if port is None:
            self.log(logging.INFO, "Warning: file .portInUse was not found. Try to fallback to default port number.")
            port_list = ["9000", "9060"]
            for port_number in port_list:
                self.log(logging.INFO, f"Try defaulting to port {port_number}...")
                test_proxy_url = self._update_port_in_url(self._base_url, port_number)
                test_proxy_result = await self.check_proxy(test_proxy_url)
                if test_proxy_result:
                    self.log(logging.INFO,
                             f"Default proxy port {port_number} was successfully checked")
                    return port_number
                self.log(logging.DEBUG, f"Default proxy port #{port_number} failed")

        if port is None:
            self.log(logging.ERROR,
                     "Error: no proxy address identified.\nCheck if Eikon Desktop or Eikon API Proxy is running.")
            return None

        self._port = port

        return port

    async def check_proxy(self, url, timeout=(15.0, 15.0)):
        url = urljoin(url, "/api/status")
        try:
            self.log(logging.INFO, f"Send GET request to {url} to detect API Proxy...")

            response = await self.http_request_async(
                method='GET',
                url=url,
                timeout=timeout,
                loop=self._loop)

            self.log(logging.INFO, f"Checking proxy url {url} response : {response.status_code} - {response.text}")
            return True
        except (socket.timeout, httpx.ConnectTimeout):
            self.log(logging.INFO, f"Timeout on checking proxy url {url}")
        except ConnectionError as e:
            self.log(logging.INFO, f"Connexion Error on checking proxy {url} : {e!r}")
        except Exception as e:
            self.log(logging.DEBUG, f"Error on checking proxy url {url} : {e!r}")
        return False

    async def handshake(self, url, timeout=(15.0, 15.0)):
        self.log(logging.INFO, f"Try to handshake on url {url}...")
        try:
            # DAPI for E4 - API Proxy - Handshake
            _body = {
                "AppKey": self.app_key,
                "AppScope": "trapi",
                "ApiVersion": "1",
                "LibraryName": "RDP Python Library",
                "LibraryVersion": __version__
            }
            if self._user_uuid:
                _body.update({"Uuid": self._user_uuid})

            _headers = {"Content-Type": "application/json"}
            response = None

            response = await self.http_request_async(
                method='POST',
                url=url,
                headers=_headers,
                json=_body,
                timeout=timeout)
            self.log(logging.INFO, f"Response : {response.status_code} - {response.text}")

            if response:
                if response.status_code == httpx.codes.OK:
                    result = response.json()
                    self._access_token = result.get("access_token")
                elif response.status_code == httpx.codes.BAD_REQUEST:
                    self.log(
                        logging.INFO,
                        f"Status code {response.status_code}: "
                        f"Bad request on handshake url {url} : {response.text}"
                    )
                    key_is_incorrect_msg = f"Status code {response.status_code}: App key is incorrect"
                    self._on_event(Session.EventCode.SessionAuthenticationFailed, None, key_is_incorrect_msg)
                    raise EikonError(1, key_is_incorrect_msg)
                else:
                    self.log(logging.DEBUG, f"Response {response.status_code} on handshake url {url} : {response.text}")

            return True
        except (socket.timeout, httpx.ConnectTimeout) as e:
            self.log(logging.ERROR, f"Timeout on handshake url {url}: {e.args}")
            raise EikonError(408, f"Timeout on handshake url {url}: {e.args}")
        except Exception as e:
            self.log(logging.ERROR, f"Error on handshake url {url} : {e!r}")
            raise EikonError(-1, f"Error on handshake url {url} : {e!r}")
        return False

    @staticmethod
    def _update_port_in_url(url, port):
        try:
            protocol, path, default_port = url.split(':')
        except ValueError:
            protocol, path, *_ = url.split(':')

        if port is not None:
            retval = ":".join([protocol, path, str(port)])
        else:
            retval = url

        return retval
