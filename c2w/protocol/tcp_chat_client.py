# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging
import struct
import ipaddress
from twisted.internet import reactor
from c2w.main.constants import ROOM_IDS


logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_client_protocol')


class c2wTcpChatClientProtocol(Protocol):

    def __init__(self, clientProxy, serverAddress, serverPort):
        """
        :param clientProxy: The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.
        :param serverAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param serverPort: The port number used by the c2w server,
            given by the user.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: clientProxy

            The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        .. attribute:: serverAddress

            The IP address of the c2w server.

        .. attribute:: serverPort

            The port number used by the c2w server.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """

        #: The IP address of the c2w server.
        self.serverAddress = serverAddress
        #: The port number used by the c2w server.
        self.serverPort = serverPort
        #: The clientProxy, which the protocol must use
        #: to interact with the Graphical User Interface.
        self.clientProxy = clientProxy
        
        self.filattente=[]
        self.host_port= (self.serverAddress,self.serverPort)
        
        self.listeFilms=[] #la liste des films envoyée par le serveur
        
        self.listeUsers=[] #la liste des utilisateurs envoyée par le serveur(Main et Movies Rooms)
        
        self.listeUsersMovie=[] #la liste des utilisateurs qui sont dans les movie room
        
        self.monNumeroSequence=0 # numero de sequence du client qui sera incrémenté au fur et à mesure
   
        self.room= " " #il s'agit de la room dans laquelle se trouve l utilisateur à un instant t
        
        self.numeroSequenceWhenGoingMovie=0 # le numero de sequence lorsque l'utilisateur fait la demande pour une movie
   
        self.numeroSequenceWhenGoingMain=0 # le numero de sequence lorsque l'utilisateur fait la demande pour revenir dans la main 
        
        self.numeroSequenceWhenOutMain=0 # le numero de sequence lorsque l'utilisateur fait la demande de deconnexion
        
        self.OnlyTitleAndIdOfMovie=[] # liste contenant les films et leur ID
        
        self.nomUtilisateur="" #contient le username de l'utilisateur
        
        self.connectivite=0
        
        # pour stocker le message recu
        self.datagram = b''
            
    #Fonction qui envoie un acuittement au serveur 
    def envoieAcquittement(self,numeroSequence):
        TypeAcq = 0
        decalage= numeroSequence << 4
        seqTypAcq= decalage | TypeAcq
        buff= struct.pack('!hh',4,seqTypAcq)
        self.transport.write(buff)
    
    #Fonction qui permet d'incrementer le numero de sequence jusqu'à 4095
    def incrementerNumeroSequence(self,numSequence):
        if (numSequence==4095): #4095= (2 exposant 12)-1
            numSequence=0
        else: 
            numSequence+=1
        return numSequence
        
    
    # fonction pour verifier si on a recu un ack
    def traiterAcquittement(self,numSeq):
       
        for p in self.filattente:
            if (p[0]==numSeq):
                p[2]=1
                print(p)
                print(self.filattente)
                print("Acquittement bien recu")
                         
    #fonction pour envoyer le paquet si jamais on a toujours pas recu d ack
    def send_And_Wait(self):
        for j in self.filattente:
            if (j[1] <= 7): # 7 correspond au nombre maximum de fois qu'on doit ramener un paquet
                if (j[2] == 0):
                    self.transport.write(j[3])
                    j[1]+=1
                    reactor.callLater(1,self.send_And_Wait)
                elif(j[2] == 1):
                    print("Confirmation acquittement bien recu")  
                    self.filattente.remove(j)        
            else:
                print("le paquet est perdu")
                self.filattente.remove(j)
                self.clientProxy.applicationQuit()   
    
    
     #Fonction pour dépaqueter la liste des films envoyée par le serveur
    def paquetListFilms(self,monpaquet):
        
        while(len(monpaquet)>0):
            #longueurMonPaquet=len(monpaquet)
            longueurFilm=int((struct.unpack('!h',monpaquet[6:8]))[0])
            print("longueur de film est :",longueurFilm," et de type :", type(longueurFilm))
            longeurTitreFilm=longueurFilm-9
            portFilm= int((struct.unpack('!h',monpaquet[4:6]))[0])
            adresseIpAConvertir=(struct.unpack('!I',monpaquet[0:4]))[0]
            adresseIp= str(ipaddress.IPv4Address(adresseIpAConvertir))
            IdMovie=int((struct.unpack('!b',monpaquet[8:9]))[0])
            titreFilm=(struct.unpack('!%is'%longeurTitreFilm,monpaquet[9:longueurFilm]))[0].decode('utf-8')
            print("film: ", titreFilm) 
            print("port :",portFilm)
            print("adresse IP : ",adresseIp,"de type", type(adresseIp))
            self.listeFilms.append((titreFilm,adresseIp,portFilm))
            self.OnlyTitleAndIdOfMovie.append([titreFilm,IdMovie])
            #print("la liste des films recu est",self.listeFilms)
            monpaquet=monpaquet[longueurFilm:]
        print("la liste des films est:", self.listeFilms)
     
    #Fonction pour dépaqueter la liste des utilisateurs envoyée par le serveur
    def paquetListUser(self,monpaquet):
        
        self.listeUsers=[]
        self.listeUsersMovie=[]
        
        while(len(monpaquet)>0):
            longueurUserName=int((struct.unpack('!b',monpaquet[0:1]))[0])
            print("longueur USERNAME est :",longueurUserName," et de type :", type(longueurUserName))
            #print("longueur USERNAME est :%i et de type : %s"%(longueurUserName, type(longueurUserName)))
            #longeurTitreFilm=longueurFilm-9
            statut= int((struct.unpack('!b',monpaquet[1:2]))[0])
            print("statut :", statut)
            nomUtilisateur= (struct.unpack('!%is'%longueurUserName,monpaquet[2:(longueurUserName+2)]))[0].decode('utf-8')
            print("USER: ", nomUtilisateur)
            
            if(statut==0):
                self.listeUsers.append((nomUtilisateur,ROOM_IDS.MAIN_ROOM))
            else:
                for k in self.OnlyTitleAndIdOfMovie:
                    if(k[1]==statut):
                        self.listeUsersMovie.append((nomUtilisateur,k[0]))
                self.listeUsers.append((nomUtilisateur,ROOM_IDS.MOVIE_ROOM))
            
            print("on a deux listes qui sont:",self.listeUsers,"\n",self.listeUsersMovie)
            
            monpaquet=monpaquet[(longueurUserName+2):]
            
    
        #Fonction permettant de former le paquet pour rejoindre une movie particulière
    def paquetForParticularMovie(self,numSequence,movieName):
        print(movieName)
        a=4+len(movieName)
        print(a)
        Type = 3
        #decalage= NumSeq << 4
        decalage= numSequence << 4
        
        seqTyp= decalage | Type
        print(seqTyp)
        buf= struct.pack('!hh%is'%len(movieName),a,seqTyp,movieName.encode('utf-8'))
        print("le paquet pour la movie room est :",buf)
        
        return buf

    #Fonction permettant de former le paquet pour retourner dans la main room
    def retourMainRoom(self,numSequence):
        Type = 4
        decalage= numSequence << 4    
        seqTyp= decalage | Type
        print(seqTyp)
        buf= struct.pack('!hh',4,seqTyp)
        print("le paquet pour la main room est :",buf)
       
        return buf
    
    #Fonction pour depaqueter un message de chat recu
    def msgChatRecu(self,monpaquet):
        longueurPseudo=int((struct.unpack('!b',monpaquet[0:1]))[0])
        pseudo=(struct.unpack('!%is'%longueurPseudo,monpaquet[1:(longueurPseudo+1)]))[0].decode('utf-8')
        sms=(struct.unpack('!%is'%(len(monpaquet)-longueurPseudo-1),monpaquet[(longueurPseudo+1):]))[0].decode('utf-8')
        print("emetteur :",pseudo, "message :", sms)
    
        return (pseudo,sms)    
    
    #Fonction permettant de former le paquet pour quitter la main room
    def quitterMainRoom(self,numSequence):
        Type = 2
        decalage= numSequence << 4    
        seqTyp= decalage | Type
        print(seqTyp)
        buf= struct.pack('!hh',4,seqTyp)
        print("le paquet pour la main room est :",buf)
       
        return buf 
    

    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The client proxy calls this function when the user clicks on
        the login button.
        """
        moduleLogger.debug('loginRequest called with username=%s', userName)
        
        self.nomUtilisateur=userName      
        print(userName)
        a=4+len(userName)
        print(a)
        #NumSeq=0
        Type = 1
  
        decalage= self.monNumeroSequence << 4
        
        seqTyp= decalage | Type
        print(seqTyp)
        buf= struct.pack('!hh%is'%len(userName),a,seqTyp,userName.encode('utf-8'))
        print(buf)
        self.transport.write(buf)
        
        self.filattente.append([self.monNumeroSequence,1,0,buf])
     
        self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)        
        
        reactor.callLater(1,self.send_And_Wait)
        

    def sendChatMessageOIE(self, message):
        """
        :param message: The text of the chat message.
        :type message: string

        Called by the client proxy when the user has decided to send
        a chat message

        .. note::
           This is the only function handling chat messages, irrespective
           of the room where the user is.  Therefore it is up to the
           c2wChatClientProctocol or to the server to make sure that this
           message is handled properly, i.e., it is shown only by the
           client(s) who are in the same room.
        """
        a=4+1+len(self.nomUtilisateur)+len(message)
        Type = 9
        decalage= self.monNumeroSequence << 4  
        seqTyp= decalage | Type
        print(seqTyp)
        buf= struct.pack('!hhb'+str(len(self.nomUtilisateur))+'s%is'%len(message),a,seqTyp,len(self.nomUtilisateur),self.nomUtilisateur.encode('utf-8'),message.encode('utf-8'))
        print("message de chat",buf)
        self.transport.write(buf)      
        
        self.filattente.append([self.monNumeroSequence,1,0,buf])
        self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)                
        reactor.callLater(1,self.send_And_Wait)
        
        pass

    def sendJoinRoomRequestOIE(self, roomName):
        """
        :param roomName: The room name (or movie title.)

        Called by the client proxy  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            The controller sets roomName to
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        
        #pour aller dans une movie room
        if (self.room== "MainRoom"):
            buf=self.paquetForParticularMovie(self.monNumeroSequence,roomName)
            self.numeroSequenceWhenGoingMovie= self.monNumeroSequence
            
            print("J'ai fait un paquet pour acceder à une movie room")

            self.transport.write(buf)
            
            self.filattente.append([self.monNumeroSequence,1,0,buf])
            self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)             
            reactor.callLater(1,self.send_And_Wait)
            self.room="MovieRoom" 
             
        #pour quitter une movie room      
        elif (self.room=="MovieRoom"):
            print("zizaggggggggggggggggggggggggggggggggggggggggggggggg")
            buf=self.retourMainRoom(self.monNumeroSequence)
            self.numeroSequenceWhenGoingMain=self.monNumeroSequence
            self.transport.write(buf) 
            
            self.filattente.append([self.monNumeroSequence,1,0,buf])
            self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
            reactor.callLater(1,self.send_And_Wait)
            self.room="MainRoom" 
            
        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
        
        buf=self.quitterMainRoom(self.monNumeroSequence)
        self.numeroSequenceWhenOutMain=self.monNumeroSequence       
        self.transport.write(buf)
        self.filattente.append([self.monNumeroSequence,1,0,buf])
        self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
        reactor.callLater(1,self.send_And_Wait)
        
        pass

    def dataReceived(self, data):
        """
        :param data: The data received from the client (not necessarily
                     an entire message!)

        Twisted calls this method whenever new data is received on this
        connection.
        """
        
        self.datagram += data
       
        while (len(self.datagram) >= 4): 
            reception=struct.unpack('!hh%is'%(len(self.datagram)-4),self.datagram)
            print(reception)
            longueur= int(reception[0])
            msgTotal= str(reception[2].decode('utf-8'))
            seqType= int(str(reception[1]))
            Type= seqType & 15
            NumSeq=seqType >> 4 
            print("la longeur est",longueur)
            print("le username est ", msgTotal)
            print("le type est ",Type)
            print("le numero de sequence est", NumSeq)
            print("la longeur est du self datagram est ",len(self.datagram))
             
            if( len(self.datagram) >= longueur): 
                print("Tout le paquet est arrivé")
                msgAttendu = self.datagram[0:longueur]
                self.datagram = self.datagram[longueur:]
                
                #traitemnts
                self.traitementTCP(msgAttendu)
                
            else:
                print("paquet en cours de chargement...")
        pass
    
    
    def traitementTCP(self, data): 
        reception=struct.unpack('!hh%is'%(len(data)-4),data)
        longueur= int(reception[0])
        msgTotal= str(reception[2].decode('utf-8'))
        corpsMessage=reception[2]
        print("le cors du msg est :",corpsMessage)
        seqType= int(str(reception[1]))
        Type= seqType & 15
        NumSeq=seqType >> 4 
        
        print("Tout le paquet est arrivé2")
        if (Type==0):
            self.traiterAcquittement(NumSeq)
            
            # après reception d'un acquittement pour rejoindre la movie room, on y va  
        
            if(NumSeq>0 and self.numeroSequenceWhenGoingMovie==NumSeq):
                print("l'utilisateur est dans la movie room")
                self.clientProxy.joinRoomOKONE()
                self.numeroSequenceWhenGoingMovie=0
                #self.room="MovieRoom" 
                #print("******************************************",self.room)
            
            # après reception d'un acquittement pour quitter la movie room, on retourne donc la main room
            if(self.numeroSequenceWhenGoingMain==NumSeq and NumSeq>0):
                print("on retourne dans la Main Room")
                self.clientProxy.joinRoomOKONE()
                self.numeroSequenceWhenGoingMain=0
                #self.room="MainRoom"
                #   print("******************************************",self.room)

            
            # Acquittement pour demande de départ du système
            if (self.numeroSequenceWhenOutMain==NumSeq and self.numeroSequenceWhenOutMain!=0 ):
                self.clientProxy.leaveSystemOKONE()
                print("BYEBYEBYEBYEBYEBYEBYEBYE")
       
         #acquittement de l'acceptation de connexion  
        if (self.connectivite==0 and Type==7):
            self.envoieAcquittement(NumSeq) # envoie de l'acquittement au serveur
            self.room= "MainRoom"
            self.connectivite=1
            print("l'utilisateur est dans la ",self.room )
        #Fin acquittement de l'acceptation de connexion 
        
        #refus de connexion
        if(Type==8):
            print("Vous n'avez pas été autorisé à vous connecter")
            self.envoieAcquittement(NumSeq)
            if(self.connectivite==0):
                self.clientProxy.connectionRejectedONE("Pseudo trop long ou déja utilisé")
                self.connectivite=1
        
         # On recoit la liste des films
        if(Type==5):
            self.envoieAcquittement(NumSeq) # envoie de l'acquittement au serveur
            self.paquetListFilms(corpsMessage)
            
        
        #On recoit la liste des utilisateurs
        if(Type==6):
            
            if(NumSeq==2):
                self.envoieAcquittement(NumSeq) # envoie de l'acquittement au serveur
                self.paquetListUser(corpsMessage)
                print("************************************",self.listeUsers) 
                print("************************************",self.listeFilms)
                self.clientProxy.initCompleteONE(self.listeUsers,self.listeFilms) #permet d'afficher la Main Room
                
            
            #cela signifie qu'il s'agit d'une mise à jour de la liste des users recue, par le serveur
            if(NumSeq>2):
                print("LE PAQUET DE MISE A JOUR DES UITILISATEUS EST ARRIVE")
                self.envoieAcquittement(NumSeq)
                self.paquetListUser(corpsMessage)
                if (self.room=="MainRoom"): 
                    print("MISE A JOUR DE LA LISTE DES UTILISATEURS DE LA MAIN ROOM")
                    print(self.listeUsers)
                    self.clientProxy.setUserListONE(self.listeUsers)
                    print("FIN MISE A JOUR DE LA LISTE DES UTILISATEURS DE LA MAIN ROOM")
                elif (self.room=="MovieRoom"):
                    print("MISE A JOUR DE LA LISTE DES UTILISATEURS DE LA MOVIE ROOM")
                    print(self.listeUsers)
                    self.clientProxy.setUserListONE(self.listeUsersMovie)            
                    print("FIN MISE A JOUR DE LA LISTE DES UTILISATEURS DE LA MOVIE ROOM")
                    
        #Lorsqu'on recoit un message de chat
        if(Type==9):
            self.envoieAcquittement(NumSeq)
            pseudo,sms=self.msgChatRecu(corpsMessage)
            if(self.nomUtilisateur!=pseudo):
                self.clientProxy.chatMessageReceivedONE(pseudo, sms)
            print("Un nouveau message")                  
            
                
         
         
         
    