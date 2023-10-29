# coding: utf8


__all__ = ["StreamingPrice"]


import sys
import logging
import re
from .itemstream import ItemStream
from .stream import StreamState
from .cache import StreamCache
from .streamingprice_callback import StreamingPriceCallback


class StreamingPrice(StreamCache):
    """
    Open a streaming price subscription.

    Parameters
    ----------
    name: string
        RIC to retrieve market prices for.

    service: string
        Specified the service to subscribe on.
        Default: None

    fields: string or list
        Specified the fields to retrieve.
        Default: None

    on_refresh: callable object (streaming_price, message)
        Called when the stream on instrument_name was opened successfully or when the stream is refreshed by the server.
        This callback is called with the reference to the streaming_price object and the instrument full image.
        Default: None

    on_update: callable object (streaming_price, message)
        Called when an update is received for a instrument_name.
        This callback is called with the reference to the streaming_price object and the instrument update.
        Default: None

    on_status: callable object (streaming_price, status)
        Called when a status is received for the stream.
        This callback is called with the reference to the streaming_price object and the instrument status.
        Default: None

    on_complete: callable object  (streaming_price)
        Called when the subscription is completed.
        This callback is called with the reference to the streaming_price object.
        Default: None

    Raises
    ------
    Exception
        If request fails or if Refinitiv Services return an error

    Examples
    --------
    >> import eikon as ek
    >> euro = ek.StreamingPrice('EUR=')
    >> euro.open()
    >> bid = euro.get_field_value('BID')
    >> ask = euro.get_field_value('ASK')
    >>
    >> def on_update(msg):
            ... print(msg)
    >> subscription = ek.StreamingPrice(['VOD.L', 'EUR=', 'PEUP.PA', 'IBM.N'],
            ... ['DSPLY_NAME', 'BID', 'ASK'],
            ... on_update=on_update)
    >> subscription.open()
    {"EUR=":{"DSPLY_NAME":"RBS          LON","BID":1.1221,"ASK":1.1224}}
    {"PEUP.PA":{"DSPLY_NAME":"PEUGEOT","BID":15.145,"ASK":15.155}}
    {"IBM.N":{"DSPLY_NAME":"INTL BUS MACHINE","BID":"","ASK":""}}
    ...
    """

    class Params(object):

        def __init__(self, *args, **kwargs):
            self._name = None
            self._service = None
            self._fields = None
            self._extended_params = None
            self._on_refresh_cb = None
            self._on_update_cb = None
            self._on_status_cb = None
            self._on_complete_cb = None
            self._on_error_cb = None

            self._domain = "MarketPrice"
            self._item_stream = None

            if len(args) > 0 and isinstance(args[0], StreamingPrice.Params):
                self.__init_from_params__(args[0])

            if kwargs:
                self._name = kwargs.get("name")
                self._service = kwargs.get("service")
                self._fields = kwargs.get("fields")
                self._extended_params = kwargs.get("extended_params")
                self._domain = kwargs.get("domain", "MarketPrice")
                self._on_refresh_cb = kwargs.get("on_refresh")
                self._on_status_cb = kwargs.get("on_status")
                self._on_update_cb = kwargs.get("on_update")
                self._on_complete_cb = kwargs.get("on_complete")
                self._on_error_cb = kwargs.get("on_error")

        def __init_from_params__(self, params):
            self._name = getattr(params, "name", None)
            self._service = getattr(params, "service", "IDN_RDF")
            self._fields = getattr(params, "fields", [])
            self._extended_params = getattr(params, "extended_params", None)
            self._on_refresh_cp= getattr(params, "on_refresh", None)
            self._on_status_cb = getattr(params, "on_status", None)
            self._on_update_cb = getattr(params, "on_update", None)
            self._on_complete_cb = getattr(params, "on_complete", None)
            self._on_error_cb = getattr(params, "on_error", None)

        def name(self, name):
            self._name = name
            return self

        def with_fields(self, fields):
            from eikon.tools import build_list
            if fields:
                self._fields = build_list(fields, 'fields')
            else:
                self._fields = None
            return self

        def with_service(self, service):
            if service:
                self._service = service
            return self

        def with_extended_params(self, extended_params):
            if extended_params:
                self._extended_params = extended_params
            return self

        def on_status(self, on_status):
            self._on_status_cb = on_status
            return self

        def on_refresh(self, on_refresh):
            self._on_refresh_cb = on_refresh
            return self

        def on_update(self, on_update):
            self._on_update_cb = on_update
            return self

        def on_complete(self, on_complete):
            self._on_complete_cb = on_complete
            return self

        def on_error(self, on_error):
            self._on_error_cb = on_error
            return self

    def __init__(self,
                 name,
                 session=None,
                 fields=None,
                 service=None,
                 streaming=None,
                 extended_params=None,
                 on_refresh=None,
                 on_status=None,
                 on_update=None,
                 on_complete=None,
                 on_error=None):
        super().__init__(name=name,
                         fields=fields,
                         service=service)

        from ..Profile import get_profile
        if session is None:
            self._session = get_profile()._desktop_session
        else:
            self._session = session
        self._extended_params = extended_params
        self._on_refresh_cb = on_refresh
        self._on_status_cb = on_status
        self._on_update_cb = on_update
        self._on_complete_cb = on_complete
        self._on_error_cb = on_error

        self._callbacks = StreamingPriceCallback()
        self._error_message = None

        if self._session is None:
            raise AttributeError("Session must be defined")
        if self._name is None:
            raise AttributeError("Instrument name must be defined.")

        self._item_stream = ItemStream(session=self._session,
                                       name=self._name,
                                       service=self._service,
                                       fields=self._fields,
                                       on_refresh=self._on_refresh,
                                       on_status=self._on_status,
                                       on_update=self._on_update,
                                       on_complete=self._on_complete,
                                       on_error=self._on_error)


    @property
    def id(self):
        return self._item_stream.stream_id


    def has_error(self):
        return self._error_message

    @property
    def state(self):
        if self._item_stream is None:
            return StreamState.Closed
        else:
            return self._item_stream.state

    @property
    def error_code(self):
        if self._item_stream is None:
            return None
        else:
            return self._item_stream._code

    @property
    def error_message(self):
        if self._item_stream is None:
            return None
        else:
            return self._item_stream._message

    ###################################################
    #  methods to open synchronously item stream      #
    ###################################################
    def open(self, with_updates=True):
        """
        Open the item stream
        """
        self._session.log(logging.DEBUG,
                          f'Open synchronously StreamingSinglePrice {self.id} to {self._name}')
        return self._item_stream.open(with_updates=with_updates)

    def close(self):
        """
        Close the data stream
        """
        self._session.log(logging.DEBUG,
                          f'Stop StreamingSinglePrice subscription {self.id} to {self._name}')
        return self._item_stream.close()

    ################################################
    #  methods to open asynchronously item stream  #
    ################################################
    async def open_async(self, with_updates=True):
        """
        Open the data stream
        """
        self._session.log(logging.DEBUG,
                          f"Open asynchronously StreamingSinglePrice {self.id} to {self._name}")
        await self._item_stream.open_async(with_updates=with_updates)

    ###################################
    # handle decoding partial update   #
    ###################################
    
    #   regular expression pattern for intra-field position sequence
    _partial_update_intra_field_positioning_sequence_regular_expression_pattern = r'[\x1b\x5b|\x9b]([0-9]+)\x60([^\x1b^\x5b|^\x9b]+)'
    _huge = 1e12

    def _decode_intra_field_position_sequence(self, cached_value, new_value):
        ''' this funciton is designed for processing intra-field positioning sequence '''

        #   find all partial update in the value
        tokens = re.findall(self._partial_update_intra_field_positioning_sequence_regular_expression_pattern, new_value)

        #   check this value contains a partial update or not?
        if len(tokens) == 0:
        #   no partial update required, so done
            return new_value
        
        #   do a partial update
        updated_value = cached_value
        for (offset, replace) in tokens:
            #   convert offset from str to int
            offset = int(offset)
            assert(offset<len(updated_value))
            
            #   replace the value in the string
            updated_value = updated_value[:offset] + replace + updated_value[offset+len(replace):]
        
        #   done, return
        return updated_value

    def _decode_partial_update_field(self, key, value):    
        ''' this function is used to proces the partial update 
                RETURNS the processed partial update data
        '''
        
        assert(isinstance(value, str))
        assert('Fields' in self._record)
        assert(key in self._record['Fields'])

        #   prevent attack when using regular expression
        assert(len(value) < self._huge)

        #   process infra-field positioning sequence
        cached_value = self._record['Fields'][key]
        updated_value = self._decode_intra_field_position_sequence(cached_value, value)
        
        #   done
        return updated_value

    ###################################
    # Messages from stream connection #
    ###################################
    def _on_refresh(self, stream, message):
        self._record = message
        if self._on_refresh_cb:
            try:
                self._on_refresh_cb(self, message["Fields"])
            except Exception as e:
                self._session.log(logging.ERROR, f'StreamingPrice on_refresh callback raised exception: {e!r}')
                self._session.log(1, f'Traceback : {sys.exc_info()[2]}')

    def _on_status(self, stream, status):
        self._status = status
        if self._on_status_cb:
            try:
                self._on_status_cb(self, status)
                self._status = status
            except Exception as e:
                self._session.log(logging.ERROR, f'StreamingPrice on_status callback raised exception: {e!r}')
                self._session.log(1, f'Traceback : {sys.exc_info()[2]}')

    def _on_update(self, stream, update):
        for data in update:
            if data == "Fields":
           #   fields data
                #   loop over all update items
                for key, value in update[data].items():
                    #   only string value need to check for a partial update
                    if isinstance(value,str):
                    #   value is a string, so check for partial update string
                        #   process partial update and update the callback with processed partial update
                        update[data][key] = self._decode_partial_update_field( key, value )

                #   update the field data
                self._record[data].update(update[data])
            else:
            #   not a "Fields" data
                self._record[data] = update[data]

        if self._on_update_cb and "Fields" in update:
            try:
                self._on_update_cb(self, update["Fields"])
            except Exception as e:
                self._session.log(logging.ERROR, f'StreamingPrice on_update callback raised exception: {e!r}')
                self._session.log(1, f'Traceback : {sys.exc_info()[2]}')

    def _on_complete(self, stream):
        if self._on_complete_cb:
            try:
                self._on_complete_cb(self)
            except Exception as e:
                self._session.log(logging.ERROR, f'StreamingPrice on_complete callback raised exception: {e!r}')
                self._session.log(1, f'Traceback : {sys.exc_info()[2]}')

    def _on_error(self, stream, error):
        if self._on_error_cb:
            try:
                self._on_error_cb(self, error)
            except Exception as e:
                self._session.log(logging.ERROR, f'StreamingPrice on_error callback raised exception: {e!r}')
                self._session.log(1, f'Traceback : {sys.exc_info()[2]}')
