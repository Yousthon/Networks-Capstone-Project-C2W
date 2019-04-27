# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import time
import struct


class SibylClientTcpBinProtocol(Protocol):
    """
    The class implementing the Sibyl TCP binary client protocol.  It has
    the following attribute:

    .. attribute:: proxy

        The reference to the SibylCientProxy (instance of the
        :py:class:`~sibyl.main.sibyl_client_proxy.SibylClientProxy` class).

        .. warning::
            All interactions between the client protocol and the user
            interface *must* go through the SibylClientProxy.  In other
            words you must call one of the methods of
            :py:class:`~sibyl.main.sibyl_client_proxy.SibylClientProxy`
            whenever you would like the user interface to do something.

    .. note::
        You must not instantiate this class.  This is done by the code
        called by the main function.

    .. note::
        You have to implement this class.  You may add any attribute and
        method that you see fit to this class.  You must implement two
        methods:
        :py:meth:`~sibyl.main.protocol.sibyl_cliend_udp_text_protocol.sendRequest`
        and
        :py:meth:`~sibyl.main.protocol.sibyl_cliend_udp_text_protocol.dataReceived`.
        See the corresponding documentation below.
    """

    def __init__(self, sibylProxy):
        """The implementation of the UDP Text Protocol.

        Args:
            sibylClientProxy: the instance of the client proxy,
                        this is the only way to interact with the user
                        interface;
        """
        self.clientProxy = sibylProxy

    def connectionMade(self):
        """
        The Graphical User Interface (GUI) needs this function to know
        when to display the request window.

        DO NOT MODIFY IT.
        """
        self.clientProxy.connectionSuccess()

    def sendRequest(self, line):
        """Called by the controller to send the request

        The :py:class:`~sibyl.main.sibyl_client_proxy.SibylClientProxy` calls
        this method when the user clicks on the "Send Question" button.

        Args:
            line (string): the text of the question

        .. warning::
            You must implement this method.  You must not change the parameters,
            as the controller calls it.

        """
    
        question = str(int(time.time()))+": "+line+"CRLF" # concatenation du temps, de la question 
        print(question)
        a=6+len(line) #la longeur totale de la trame (4+2+taille de la question)
        """le temps est sur 4 octets
            la longueur de la trame est sur 2 octets """
        buf= struct.pack('ih%is'%len(line),int(time.time()),a,line.encode('utf-8')) 
        print(buf)
        self.transport.write(buf)
        
        pass

    def dataReceived(self, line):
        """Called by Twisted whenever a data is received

        Twisted calls this method whenever it has received at least one byte
        from the corresponding TCP connection.

        Args:
            line (bytes): the data received (can be of any length greater than
            one);

        .. warning::
            You must implement this method.  You must not change the parameters,
            as Twisted calls it.

        """
        self.clientProxy.responseReceived(line.decode("utf-8")) #affiche de la reponse sur l'interface
        print(line.decode("utf-8"))
        pass
    