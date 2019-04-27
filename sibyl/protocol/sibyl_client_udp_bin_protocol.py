# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
import time
import struct

class SibylClientUdpBinProtocol(DatagramProtocol):
    """
        The class implementing the Sibyl client protocol.  It has
        the following attributes:

        .. attribute:: proxy

            The reference to the SibylCientProxy (instance of the
            :py:class:`~sibyl.main.sibyl_client_proxy.SibylClientProxy` class).

            .. warning::
                All interactions between the client protocol and the user
                interface *must* go through the SibylClientProxy.  In other
                words you must call one of the methods of
                :py:class:`~sibyl.main.sibyl_client_proxy.SibylClientProxy` whenever
                you would like the user interface to do something.

        .. attribute:: serverAddress  self.transport.connect(self.serverAddress,self.serverPort)
        reponse = str(int(time.time()))+": "+line+"CRLF"
        #print(reponse)
        buf= struct.pack('IH100s',int(time.time()),len(line),line.encode('utf-8'))
        print(buf)
        self.transport.write(buf)

            The address of the server.

        .. attribute:: serverPort

            The port number of the server.

        .. note::
            You must not instantiate this class.  This is done by the code
            called by the main function.

        .. note::
            You have to implement this class.  You may add any attribute and
            method that you see fit to this class.  You must implement two
            methods:
            :py:meth:`~sibyl.main.protocol.sibyl_cliend_udp_text_protocol.sendRequest`
            and
            :py:meth:`~sibyl.main.protocol.sibyl_cliend_udp_text_protocol.datagramReceived`.
            See the corresponding documentation below.
        """

    def __init__(self, sibylClientProxy, port, host):
        """The implementation of the UDP Text Protocol.

        Args:
            sibylClientProxy: the instance of the client proxy,
                        this is the only way to inte  self.transport.connect(self.serverAddress,self.serverPort)
        reponse = str(int(time.time()))+": "+line+"CRLF"
        #print(reponse)
        buf= struct.pack('IH100s',int(time.time()),len(line),line.encode('utf-8'))
        print(buf)
        self.transport.write(buf)ract with the user
                        interface;
            port: the port number of the server;
            host: the address of the server.
        """
        self.serverAddress = host
        self.serverPort = port
        self.clientProxy = sibylClientProxy

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
        self.transport.connect(self.serverAddress,self.serverPort) #connection au serveur
        question = str(int(time.time()))+": "+line+"CRLF" # concatenation du temps, de la question 
        print(question)
        a=6+len(line) #la longeur totale de la trame (4+2+taille de la question)
        """le temps est sur 4 octets
            la longueur de la trame est sur 2 octets """
        buf= struct.pack('IH%is'%len(line),int(time.time()),a,line.encode('utf-8')) 
        print(buf)
        self.transport.write(buf)

        pass

    def datagramReceived(self, datagram, host):
        """Called by Twisted whenever a datagram is received

        Twisted calls this method whenever a datagram is received.

        Args:
            datagram (bytes): the payload of the UPD packet;
            host_port (tuple): the source host and port number.

        .. warning::
            You must implement this method.  You must not change the parameters,
            as Twisted calls it.

        """
        self.clientProxy.responseReceived(datagram.decode("utf-8")) #affiche de la reponse sur l'interface du client
        print(datagram.decode("utf-8"))
        pass
    