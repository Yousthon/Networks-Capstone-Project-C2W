# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import struct,math,time


class SibylServerTimerUdpBinProtocol(DatagramProtocol):
    """The class implementing the Sibyl UDP binary server protocol.

        .. note::
            You must not instantiate this class.  This is done by the code
            called by the main function.

        .. note::

            You have to implement this class.  You may add any attribute and
            method that you see fit to this class.  You must implement the
            following method (called by Twisted whenever it receives a
            datagram):
            :py:meth:`~sibyl.main.protocol.sibyl_server_udp_bin_protocol.datagramReceived`
            See the corresponding documentation below.

    This class has the following attribute:

    .. attribute:: SibylServerProxy

        The reference to the SibylServerProxy (instance of the
        :py:class:`~sibyl.main.sibyl_server_proxy.SibylServerProxy` class).

            .. warning::

                All interactions between the client protocol and the server
                *must* go through the SibylServerProxy.

    """

    def __init__(self, sibylServerProxy):
        """The implementation of the UDP server text protocol.

        Args:
            sibylServerProxy: the instance of the server proxy.
        """
        self.sibylServerProxy = sibylServerProxy



    def datagramReceived(self, datagram, host_port):
        """Called by Twisted whenever a datagram is received

        Twisted calls this method whenever a datagram is received.

        Args:
            datagram (bytes): the payload of the UPD packet;
            host_port (tuple): the source host and port number.

            .. warning::
                You must implement this method.  You must not change the
                parameters, as Twisted calls it.
        """
        
        taille=len(datagram)-6
        reception=struct.unpack('IH%is'%taille,datagram)
        print(reception)
        #print("type de reception",type(reception))
        ts = str(reception[0])
        envoie= self.sibylServerProxy.generateResponse(reception[2].decode('utf-8'))
        msg = "%s: %s"%(ts, envoie)
        print(msg)
        
        delay = math.ceil(math.log(reception[1]))
        #time.sleep(delay)
        self.transport.connect(host_port[0],host_port[1])
        #self.transport.write(envoie.encode('utf-8'))
        
        reactor.callLater(delay, self.transport.write, msg.encode('utf-8'))
        #reactor.run()
        
        pass
    
"""reactor.listenUDP(host_port[1], SibylServerTimerUdpBinProtocol())
reactor.run() """
