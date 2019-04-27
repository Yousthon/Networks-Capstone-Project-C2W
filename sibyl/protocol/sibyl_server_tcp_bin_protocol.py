# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import time
import struct

class SibylServerTcpBinProtocol(Protocol):
    """The class implementing the Sibyl TCP binary server protocol.

        .. note::
            You must not instantiate this class.  This is done by the code
            called by the main function.

        .. note::

            You have to implement this class.  You may add any attribute and
            method that you see fit to this class.  You must implement the
            following method (called by Twisted whenever it receives data):
            :py:meth:`~sibyl.main.protocol.sibyl_server_tcp_bin_protocol.dataReceived`
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
        
        
        def verifier_data(taille,line):
        
            flag = 0
            
            if(len(line) >= 6): 
                taille_pk = struct.unpack('h', line[4:6])# recuperation du nombre de paquet
                    
                if(taille_pk[0] == len(line)): 
                    msg = struct.unpack('%is'%taille, line[6:])# recuperation du nombre de paquet
                        
                    if(len(msg[0]) == taille): 
                            flag = 1
                    else:
                        return flag
                        
                else:
                    return flag
                
            else:
                return flag
            
            return flag
        
        taille=len(line)-6 # la variable est la taille de la question du client proprement dite
        flag = verifier_data(taille,line) # on teste ce qu'on a recu
        
        if (flag == 1): 
            reception=struct.unpack('ih%is'%taille, line)
            print(reception)# la variable reception est un tuple de taille 3 (temps,taille de la trame,question)
            ts = str(reception[0])
            envoie= self.sibylServerProxy.generateResponse(reception[2].decode('utf-8'))
            msg = "%s: %s"%(ts, envoie)
            self.transport.write(msg.encode('utf-8'))
        
        else:
            pass
        
