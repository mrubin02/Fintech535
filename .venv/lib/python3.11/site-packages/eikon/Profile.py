# coding: utf-8

__all__ = ['set_app_key', 'get_app_key',
           'set_timeout', 'get_timeout',
           'set_port_number', 'get_port_number',
           'set_log_level', 'set_log_path',
           'set_on_state_callback', 'set_on_event_callback',
           'Profile', 'get_desktop_session']


import deprecation
import logging

from .tools import is_string_type
from .eikonError import EikonError
from eikon import __version__
from .streaming_session import DesktopSession


def set_app_key(app_key):
    """
    Set the app key.

    Parameters
    ----------
    app_key : string
        the app key
    Notes
    -----
    The app key identifies your application on Refinitiv Platform.
    You can get an app key using the App Key Generator (this App is available in Eikon Desktop).
    """
    get_profile().set_app_key(app_key)


def get_app_key():
    """
    Returns the app key previously set

    Notes
    -----
    The app key identifies your application on Refinitiv Platform.
    You can get an application ID using the App Key Generator (this App is available in Eikon Desktop).
    """
    return get_profile().get_app_key()


def get_desktop_session():
    """
    Returns the desktop session for streaming access

    Notes
    -----
    The desktop session is use to initialize streaming subscription.
    """
    return get_profile()._get_desktop_session()


def set_on_state_callback(on_state):
    """
    Set the callback for desktop session state notification.

    Parameters
    ----------
    on_state : function that accepts session, state_ and state_msg as parameters.
    """
    get_profile().set_on_state_callback(on_state)


def set_on_event_callback(on_event):
    """
    Set the callback for desktop session event notification.

    Parameters
    ----------
    on_event : function that accepts session, event_code and event_msg as parameters.
    """
    get_profile().set_on_event_callback(on_event)


def set_timeout(timeout):
    """
    Set the timeout for each request.

    Parameters
    ----------
    timeout : int
        the request timeout in sec
        Default value: 30 sec
    """
    get_profile().set_timeout(timeout)


def get_timeout():
    """
    Returns the request timeout in sec
    """
    return get_profile().get_timeout()


def set_port_number(port_number):
    """
    Set the port number to communicate with the Eikon Data API proxy.
    This port number is detected automatically but you can call this function to force it manually for troubleshooting issues.

    Parameters
    ----------
    port_number : int
        the port number
    """
    get_profile().set_port_number(port_number)


def get_port_number():
    """
    Returns the port number used to communicate with the Eikon Data API Proxy
    """
    return get_profile().get_port_number()


def get_profile():
    """
    Returns the Profile singleton
    """
    return Profile.get_profile()


def set_log_level(level):
    """
    Set the log level.
    When logs are activated (log_level != logging.NOTSET), log files are created in the current directory.
    To change directory for log files, set log path with set_log_path() function.

    Parameters
    ----------
    level : int
        Possible values from logging module : [CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET]

    Example
    -------
        ek.set_log_level(logging.DEBUG)

    """
    get_profile().set_log_level(level)


def set_log_path(path):
    """
    Set the filepath of the log file.

    Parameters
    ----------
    path : string
        File path location for log files

    Example
    -------
        ek.set_log_path("c:\\my_directory")
    """
    get_profile().set_log_path(path)


class Profile(object):

    TRACE = 5
    MAX_LOG_SIZE = 10000000

    # singleton profile
    __profile = None

    @classmethod
    def get_profile(cls):
        """
        Returns the Profile singleton
        """
        if cls.__profile is None:
            cls.__profile = Profile()
        return cls.__profile

    def __init__(self):
        """
        Initialization of the __profile.
        """
        self.log_path = None
        self.log_level = logging.NOTSET

        logging.addLevelName(5, 'TRACE')
        self.logger = logging.getLogger('pyeikon')
        setattr(self.logger, 'trace', lambda *args: self.logger.log(5, *args))

        self.app_key = None
        self._desktop_session = None
        self._on_state_cb = None
        self._on_event_cb = None

        self.url = None
        self.streaming_url = None
        self.timeout = None

        self.log_level = logging.NOTSET

    def __del__(self):
        print('Delete a Profile')

    def __delete__(self, instance):
        self.log(1, f'Delete the Profile instance {instance}')

    def set_app_key(self, app_key):
        """
        Set the application id.
        """
        if app_key is None:
            raise AttributeError('App key value is None')
        else:
            if not is_string_type(app_key):
                raise AttributeError('App key must be a string')

            if self._desktop_session:
                self.logger.debug('Reset a Desktop session with new app_key')
                self._desktop_session.close()
                self._desktop_session._app_key = app_key  # = DesktopSession(app_key, self._on_state, self._on_event)
            else:
                self._desktop_session = DesktopSession(app_key=app_key,
                                                       on_state= self._on_state,
                                                       on_event=self._on_event)
            self._desktop_session.set_log_level(self.log_level)
            self._desktop_session.set_timeout(self.timeout)
            self._desktop_session.open()
            self.logger = self._desktop_session.logger()
            self.logger.debug('Init a Desktop session with new app_key')

    def set_on_state_callback(self, on_state):
        self._on_state_cb = on_state

    def set_on_event_callback(self, on_event):
        self._on_event_cb = on_event

    def _on_state(self, session, state_code, state_msg):
        if self._on_state_cb:
            self._on_state_cb(self, state_code, state_msg)

    def _on_event(self, session, event_code, event_msg):
        if self._on_event_cb:
            self._on_event_cb(self, event_code, event_msg)

    def _get_desktop_session(self):
        if self._desktop_session:
            return self._desktop_session
        else:
            raise EikonError(-1, "Set app_key is mandatory first !")

    def get_app_key(self):
        """
        Returns the app key.
        """
        return self._get_desktop_session().app_key

    def get_url(self):
        """
        Returns the scripting proxy url.
        """
        return self._get_desktop_session()._get_udf_url()

    def get_streaming_url(self):
        """
        Returns the streaming_session proxy url.
        """
        return self._get_desktop_session()._streaming_config.url

    def _get_http_session(self):
        """
        Returns the scripting proxy _http_session for requests.
        """
        return self._get_desktop_session()._get_http_session()

    def set_timeout(self, timeout):
        """
        Set the timeout in seconds for each request.
        """
        self.timeout = timeout
        if self._desktop_session:
            self._get_desktop_session().set_timeout(timeout=timeout)

    def get_timeout(self):
        """
        Returns the timeout for requests.
        """
        if self._desktop_session:
            return self._get_desktop_session().get_timeout()
        else:
            return self.timeout

    @deprecation.deprecated(deprecated_in="1.1.3", removed_in="1.2",
                            current_version=__version__,
                            details="Port number is detected automatically.")
    def set_port_number(self, port_number):
        """
        Set the port number to reach Eikon API proxy.
        """
        pass

    @property
    def port(self):
        return self._get_desktop_session().get_port_number()

    def get_port_number(self):
        """
        Returns the port number
        """
        return self._get_desktop_session().get_port_number()

    def set_log_path(self, log_path):
        """
        Set the path where log files will be created.

        Parameters
        ----------
        log_path : path directory
            Default: current directory (beside *.py running file)
        Return True if log_path exists and is writable
        """
        return self._get_desktop_session().set_log_path(log_path)

    def set_log_level(self, log_level):
        """
        Set the log level.
        By default, logs are disabled.

        Parameters
        ----------
        log_level : int
            Possible values from logging module : [CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET]
        """
        self.log_level = log_level
        if self._desktop_session:
            self._get_desktop_session().set_log_level(log_level)

    def get_log_level(self):
        """
        Returns the log level
        """
        if self._desktop_session:
            return self._get_desktop_session().get_log_level()
        else:
            return self.log_level

    def send_request(self, json, timeout=None):
        response = self._desktop_session.http_request(url=self.get_url(),
                                                      method="POST",
                                                      headers={'Content-Type': 'application/json',
                                                               'x-tr-applicationid': self.get_app_key()},
                                                      json=json,
                                                      timeout=timeout)
        return response
