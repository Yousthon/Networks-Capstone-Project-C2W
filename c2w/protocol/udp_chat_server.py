# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
from twisted.internet import reactor
import logging
import struct
import ipaddress
from c2w.main.constants import ROOM_IDS

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_server_protocol')


class c2wUdpChatServerProtocol(DatagramProtocol):

    def __init__(self, serverProxy, lossPr):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
        :param lossPr: The packet loss probability for outgoing packets.  Do
            not modify this value!

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: lossPr

            The packet loss probability for outgoing packets.  Do
            not modify this value!  (It is used by startProtocol.)

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """
        #: The serverProxy, which the protocol must use
        #: to interact with the server (to access the movie list and to 
        #: access and modify the user list).
        self.serverProxy = serverProxy
        self.lossPr = lossPr
        self.filattente=[]
        self.nom="" #sauvegarde de temporairement le nom de utilisateur lors de sa demande de connexion
        
        self.monNumeroSequence=0 # numero de sequence du serveur qui sera incrémenté au fur et à mesure        
        
        # sauvegarde pour chaque utilisateur le couple (host_port,numero de sequence attendu)
        self.controlNumeroSequence=[] 
    
    #Fonction qui permet d'incrementer le numero de sequence jusqu'à 4095
    def incrementerNumeroSequence(self,numSequence):
        if (numSequence==4095): #4095= (2 exposant 12)-1
            numSequence=0
        else: 
            numSequence+=1
        return numSequence

    # fonction pour verifier si on a recu un acquittement
    def traiterAcquittement(self,numSeq,hostPort):      
        for j in self.filattente:                  
            if (j[4]==hostPort):
                if (j[0]==numSeq):
                    j[2]=1
                    print("Acquittement bien recu")    
    
    #fonction pour envoyer le paquet si jamais on a toujours pas recu d ack
    def send_And_Wait(self,hostPort):
        for j in self.filattente:
            if (j[4]==hostPort):                  
                if (j[1] <= 7):
                    if (j[2] == 0):
                        self.transport.write(j[3],j[4])
                        j[1]+=1
                        reactor.callLater(1,self.send_And_Wait,j[4])  
                    elif(j[2] == 1):
                        print("etat de la liste avant suppression",self.filattente)
                        self.filattente.remove(j) 
                        print("etat de la liste apres suppression",self.filattente)
                        
                else:
                    print("le paquet a djaaaaaaa")
                    self.filattente.remove(j)
                    if(len(self.serverProxy.getUserList())!=0):
                        
                        user = self.serverProxy.getUserByAddress(hostPort)
                        print(user)
                        print("Supprimons l'utilisateur car il ne repond plus")
                          
                        self.serverProxy.updateUserChatroom(user.userName,ROOM_IDS.OUT_OF_THE_SYSTEM_ROOM)                 
                        self.serverProxy.removeUser(self.serverProxy.getUserByAddress(hostPort).userName)                
                        
                        for u in self.controlNumeroSequence:
                            if(u[0]==hostPort):
                                self.controlNumeroSequence.remove(u)    
                    
                        print("SUCCES DE LA SUPPRESSION DU USER") 
                        
                        #Mise à jour de la liste des utilisateurs
                        #le paquet sera envoyé à chaque utilisateur de la main room
                        for u in self.serverProxy.getUserList():
                            if (u.userChatRoom==ROOM_IDS.MAIN_ROOM):    
                                print("le paquet sera envoyé à chaque utilisateur de la main room")
                                bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MAIN_ROOM)
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                self.transport.write(bufserver,u.userAddress)
                                print("le paquet est",bufserver)                         
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                                print("MISE A JOUR TERMINEE ")
                            
                            else:
                                print("le paquet sera envoyé à chaque utilisateur de la movie room")
                                bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MOVIE_ROOM)
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                self.transport.write(bufserver,u.userAddress)
                                print("le paquet est",bufserver)                         
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                                print("MISE A JOUR TERMINEE ")
                            
                        print("YOUPIIIIIIIIIIIIII")
   
   #fonction pour construire le paquet pour la liste des films
       
    def paquetListFilms(self):
        paquetMovie=bytearray()
        compteur=0
        print("////////////////////////////////////////",self.serverProxy.getMovieList())
        for k in self.serverProxy.getMovieList():
            longueurFilm= 0
            ipFilm=k.movieIpAddress
            convIpFilm=int(ipaddress.IPv4Address(ipFilm)) #convertit l'adresse ip en un entier
            portFilm=k.moviePort 
            idFilm=k.movieId
            print("l'identifiant du film est :",idFilm)
            titreFilm=k.movieTitle
            longueurFilm= 9+len(titreFilm)
            compteur=compteur+longueurFilm
            paquetMovie+=struct.pack('!Ihhb%rs'%len(titreFilm),convIpFilm,portFilm,longueurFilm,idFilm,titreFilm.encode('utf-8'))
        
        print("le corps est :",paquetMovie)
        TypEnvoieFilm= 5
        NumSeq=1
        seqTypEnvoieFilm= (NumSeq << 4) | TypEnvoieFilm
        compteur= compteur+4
        entete=struct.pack('!hh',compteur,seqTypEnvoieFilm)
        paquetTotal=entete+paquetMovie
        print("l'entete est :",entete)
        print("le paquet total est:",paquetTotal)
    
        return paquetTotal

    
    # fonction pour former le paquet de la liste des utilisateurs
    def paquetListUser(self,numSeq,room):
        paquetUserMain=bytearray()     
        paquetUserM=bytearray()  
        paquetOnlyUserInMovie=bytearray()
        
        """la variable suivante contiendra soit les utilisateurs dans la main room
        et ceux de toutes les movies room ou soit d'une movie room specifique """
        paquetUserFinal=bytearray() 
         
        compteur=0
        
        # construction de paquet en direction de la main room
        if (room==ROOM_IDS.MAIN_ROOM):
            for u in self.serverProxy.getUserList():
                print("la liste des users pour c2w est:",self.serverProxy.getUserList())                              
                if(u.userChatRoom==ROOM_IDS.MAIN_ROOM):                   
                    statut=0
                    nomUtilisateurA=u.userName
                    #compteur=compteur+2+len(usernameA)                           
                    paquetUserMain+=struct.pack('!bb%is'%len(nomUtilisateurA),len(nomUtilisateurA),statut,nomUtilisateurA.encode('utf−8'))   
                else:                    
                    statut=1
                    nomUtilisateurM=u.userName
                    #compteur=compteur+2+len(usernameM)                           
                    paquetUserM+=struct.pack('!bb%is'%len(nomUtilisateurM),len(nomUtilisateurM),statut,nomUtilisateurM.encode('utf−8'))   
            paquetUser=paquetUserMain+paquetUserM                   
            paquetUserFinal=paquetUser 
        
        # construction de paquet en direction d'une movie room
        else :
             for u in self.serverProxy.getUserList():         
                if (u.userChatRoom!=ROOM_IDS.MAIN_ROOM ):
                    for m in self.serverProxy.getMovieList():
                        if(m.movieTitle==u.userChatRoom):
                            
                            statut=m.movieId
                            nomUtilisateurMovie=u.userName
                            print("//////////////////////////////////////////",nomUtilisateurMovie,"movieid",statut)
                            paquetOnlyUserInMovie+=struct.pack('!bb%is'%len(nomUtilisateurMovie),len(nomUtilisateurMovie),statut,nomUtilisateurMovie.encode('utf−8'))   
             
             paquetUserFinal=paquetOnlyUserInMovie 
        
        print("le corps du paquet utilisateur est :",paquetUserFinal)
        TypEnvoieUser= 6
   
        seqTypEnvoieFilm= (numSeq << 4) | TypEnvoieUser
        compteur= len(paquetUserFinal)+4
        entete=struct.pack('!hh',compteur,seqTypEnvoieFilm) # construction de l'entete
        paquetTotal=entete+paquetUserFinal 
        print("l'entete est :",entete)
        print("lepaquet total est:",paquetTotal) 
        
        return paquetTotal
    
        
    def startProtocol(self):
        """
        DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

        If in doubt, do not add anything to this method.  Just ignore it.
        It is used to randomly drop outgoing packets if the -l
        command line option is used.
        """
        self.transport = LossyTransport(self.transport, self.lossPr)
        DatagramProtocol.transport = self.transport

    def datagramReceived(self, datagram, host_port):
        """
        :param string datagram: the payload of the UDP packet.
        :param host_port: a touple containing the source IP address and port.
        
        Twisted calls this method when the server has received a UDP
        packet.  You cannot change the signature of this method.
        """
        
        reception=struct.unpack('!hh%is'%(len(datagram)-4),datagram)
        print(reception)
        longueur= str(reception[0])
        username= str(reception[2].decode('utf-8'))
        #self.user.append(username)
        seqType= int(str(reception[1]))
        Type= seqType & 15
        NumSeq=seqType >> 4 
        print("la longeur est",longueur)
        print("le username est ", username)
        print("le type est ",Type)
        print("le numero de sequence est", NumSeq)
        
        #permet de definir le numero de sequence attendu pour chaque utilisateur
        if(len(self.controlNumeroSequence)!=0):
            for u in self.controlNumeroSequence:
                if(u[0]==host_port):
                    if (Type==3 or Type==4 or Type==9):
                        u[1]+=1
                        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",u[1])
            
        
        # cette portion est exécutée lorsqu'on reçoit un acquittement
        if(Type==0):
            self.traiterAcquittement(NumSeq,host_port)
            
        
        # On envoie une acceptation ou un refus de connexion après la demande de connexion du client

        if (Type==1):
            
            self.nom=username
            TypeAcq = 0
            decalage= NumSeq << 4
            seqTypAcq= decalage | TypeAcq
            print("sequence et type concaténé pour le 1er acquittement est", seqTypAcq)
            bufserver= struct.pack('!hh',4,seqTypAcq)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            #fin premier acquittement après reception
            
            
            """ s il depasse le nombre de caractere permis ou si le pseudo est déja 
            utilisé, on lui envoie un message d erreur"""
            
            if(len(self.nom)>251 or self.serverProxy.userExists(self.nom)):
                TypeRejectConn= 8
                monNumSeq=0
                seqTypRejectConn= (monNumSeq << 4) | TypeRejectConn
                bufserver= struct.pack('!hh',4,seqTypRejectConn)
                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)    
                self.transport.write(bufserver,host_port)
                print(self.serverProxy.getUserList())  
                self.filattente.append([0,1,0,bufserver,host_port])
                reactor.callLater(1,self.send_And_Wait,host_port)
            
            #Acceptation de connexion
            else:
                TypeAccepetConn= 7
                monNumSeq=0
                
                seqTypAccepetConn= (monNumSeq << 4) | TypeAccepetConn
                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                
                print("sequence et type concaténé pour l'acceptation est",seqTypAccepetConn)
                bufserver= struct.pack('!hh',4,seqTypAccepetConn)
                self.transport.write(bufserver,(host_port[0],host_port[1]))

                self.filattente.append([0,1,0,bufserver,host_port])
                reactor.callLater(1,self.send_And_Wait,host_port)
            #Fin Acceptation de connexion
                
                
                #print(self.serverProxy.getUserByAddress(host_port[0]))
                """for m in self.serverProxy.getMovieList():
                    print("Movie title: ", m.movieTitle)"""
           
                               
           
        # On envoie la liste des films
        
        if(Type==0 and NumSeq==0):
            print("oooooooooooooooooooooooooooooooooooooaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            
            """ipFilm0=self.serverProxy.getMovieList()[0].movieIpAddress
            portFilm0=self.serverProxy.getMovieList()[0].moviePort
            idFilm0=self.serverProxy.getMovieList()[0].movieId"""
            
            #Ajout de l'utilisateur à la liste gérée par le serveur
            self.serverProxy.addUser(self.nom,ROOM_IDS.MAIN_ROOM,None,host_port) 
            
            #Ajout de l'utilisateur à la liste de controle gérée par nous-meme
            self.controlNumeroSequence.append([host_port,0])
            
            # On informe les autres utilisateurs qui sont dans la main room de l'arrivée du nouveau
            if(len(self.serverProxy.getUserList())>0):
                newUser = self.serverProxy.getUserByAddress(host_port).userName
                print("BIENVENUE",newUser)
                for u in self.serverProxy.getUserList():
                    if (u.userChatRoom==ROOM_IDS.MAIN_ROOM):
                        if (u.userName != newUser ) :
                            print("le paquet sera envoyé à chaque utilisateur de la main room")
                            paquet=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MAIN_ROOM)
                            self.filattente.append([self.monNumeroSequence,1,0,paquet,u.userAddress])
                            self.transport.write(paquet,u.userAddress)
                            print("le paquet est",paquet)                         
                            self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                            reactor.callLater(1,self.send_And_Wait,u.userAddress)  
            
            print("la liste des users pour c2w est:",self.serverProxy.getUserList())
            print("il ya dans la liste", len(self.serverProxy.getUserList()))
            print("un utilisateur lambda dans la liste des users pour c2w est:",self.serverProxy.getUserList()[0].userName)
            print("********************************",self.nom)
            bufserver=self.paquetListFilms()
            self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            self.filattente.append([1,1,0,bufserver,host_port])
            reactor.callLater(1,self.send_And_Wait,host_port)
            
        # On envoie la liste des utilisateurs
        if (Type==0 and NumSeq==1):
            print("zezezezezezezezezezezezezezezezezezezezeezezezezezeze")
            #print(ROOM_IDS.MAIN_ROOM)
            bufserver=self.paquetListUser(2,ROOM_IDS.MAIN_ROOM)
            self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            self.filattente.append([2,1,0,bufserver,host_port])
            reactor.callLater(1,self.send_And_Wait,host_port)
        
        #Lorsqu'on recoit une demande pour acceder à la movie room
        if(Type==3):
            print("DEMANDE D'ACCES A UNE MOVIE ROOM")
            
            #envoie de l'acquittement  
            
            TypeAcq = 0
            decalage= NumSeq << 4
            seqTypAcq= decalage | TypeAcq
            print("sequence et type concaténé pour le 1er acquittement est", seqTypAcq)
            bufserver= struct.pack('!hh',4,seqTypAcq)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            
            # Fin de l'envoie de l'acquittement            
            
            for u in self.controlNumeroSequence:
                if(u[0]==host_port and u[1]==NumSeq):
                
                    nameOfRoom=str(reception[2].decode('utf-8')) 
                    #self.roomName=roomName
                    user=self.serverProxy.getUserByAddress(host_port)
                    if(user.userChatRoom==ROOM_IDS.MAIN_ROOM):
                        print("il y a un utilisateur qui veut regarder :"+nameOfRoom)
                        
                        
                        self.serverProxy.startStreamingMovie(nameOfRoom)
                        
                        
                        username = self.serverProxy.getUserByAddress(host_port).userName
                        print(username)
                        print(host_port)
                        self.serverProxy.updateUserChatroom(username,nameOfRoom)
                        
                        #Mise à jour des la liste des utilisateurs
                        print("la liste des users MAJ pour c2w est:",self.serverProxy.getUserList())
                        for u in self.serverProxy.getUserList():
                            
                            #paquet en direction des users de la main room
                            if (u.userChatRoom==ROOM_IDS.MAIN_ROOM):    
                                print("le paquet sera envoyé à chaque utilisateur de la main room")
                                bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MAIN_ROOM)
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                self.transport.write(bufserver,u.userAddress)
                                print("le paquet est",bufserver)                         
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                            
                            #paquet en direction des users des movies room 
                            else:
        
                                print("le paquet sera envoyé à chaque utilisateur de la movie room")
                                bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MOVIE_ROOM)
                                print("le paquet est",bufserver)                        
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                self.transport.write(bufserver,u.userAddress)
                                print("le paquet est",bufserver)                        
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                
                elif(u[0]==host_port):
                    u[1]-=1
                         
            
            
        #Lorsqu'on recoit une demande pour retourner dans la main room
        if(Type==4):
            print("DEMANDE DE RETOUR A LA MAIN ROOM")
            
            #envoie de l'acquittement  
            TypeAcq = 0
            decalage= NumSeq << 4
            seqTypAcq= decalage | TypeAcq
            print("sequence et type concaténé pour le 1er acquittement est", seqTypAcq)
            bufserver= struct.pack('!hh',4,seqTypAcq)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            #Fin de l'envoie de l'acquittement            
            
            for u in self.controlNumeroSequence:
                if(u[0]==host_port and u[1]==NumSeq):
                    
                    user=self.serverProxy.getUserByAddress(host_port)
                    if(user.userChatRoom!=ROOM_IDS.MAIN_ROOM):
                        print("il y a un utilisateur qui quitte une movie room")
                        
                        
                        self.serverProxy.stopStreamingMovie(user.userChatRoom)
                        
                        
                        username = self.serverProxy.getUserByAddress(host_port).userName
                        print(username)
                        print(host_port)
                        self.serverProxy.updateUserChatroom(username,ROOM_IDS.MAIN_ROOM)
                        
                        #Mise à jour des la liste des utilisateurs
                        print("la liste des users MAJ pour c2w est:",self.serverProxy.getUserList())
                        for u in self.serverProxy.getUserList():
                            
                            #paquet en direction des users de la main room
                            if (u.userChatRoom==ROOM_IDS.MAIN_ROOM):    
                                print("le paquet sera envoyé à chaque utilisateur de la main room")
                                bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MAIN_ROOM)
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                self.transport.write(bufserver,u.userAddress)
                                print("le paquet est",bufserver)                         
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                             
                            #paquet en direction des users des movies room 
                            else:
        
                                print("le paquet sera envoyé à chaque utilisateur de la movie room")
                                bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MOVIE_ROOM)
                                print("le paquet est",bufserver)                        
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                self.transport.write(bufserver,u.userAddress)
                                print("le paquet est",bufserver)                        
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                
                elif(u[0]==host_port):
                    u[1]-=1
        
        #on recoit une demande de déconnexion
        if(Type==2):
            #envoie de l'acquittement
            TypeAcq = 0
            decalage= NumSeq << 4
            seqTypAcq= decalage | TypeAcq
            print("sequence et type concaténé pour le 1er acquittement est", seqTypAcq)
            bufserver= struct.pack('!hh',4,seqTypAcq)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            #Fin envoie de l'acquittement            
            
            user = self.serverProxy.getUserByAddress(host_port)
            
            if(user.userChatRoom==ROOM_IDS.MAIN_ROOM):
                print("Supprimons l'utilisateur")
                  
                self.serverProxy.updateUserChatroom(user.userName,ROOM_IDS.OUT_OF_THE_SYSTEM_ROOM)                 
                self.serverProxy.removeUser(self.serverProxy.getUserByAddress(host_port).userName)                
                
                for u in self.controlNumeroSequence:
                    if(u[0]==host_port):
                        self.controlNumeroSequence.remove(u)    
                
                print("on a une demande de déconnexion") 
                
                #le paquet sera envoyé à chaque utilisateur de la main room
                for u in self.serverProxy.getUserList():
                    if (u.userChatRoom==ROOM_IDS.MAIN_ROOM):    
                        print("le paquet sera envoyé à chaque utilisateur de la main room")
                        bufserver=self.paquetListUser(self.monNumeroSequence,ROOM_IDS.MAIN_ROOM)
                        self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                        self.transport.write(bufserver,u.userAddress)
                        print("le paquet est",bufserver)                         
                        self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                        reactor.callLater(1,self.send_And_Wait,u.userAddress)
                     
        
        #on recoit un message de chat qu'on doit diffuser aux utilisateurs de la meme room        
        if(Type==9):
            #Envoie de l'acquittement
            TypeAcq = 0
            decalage= NumSeq << 4
            seqTypAcq= decalage | TypeAcq
            print("sequence et type concaténé pour le 1er acquittement est", seqTypAcq)
            bufserver= struct.pack('!hh',4,seqTypAcq)
            self.transport.write(bufserver,(host_port[0],host_port[1]))
            # Fin Envoie de l'acquittement
            
            for u in self.controlNumeroSequence:
                #Pour l'emetteur,on compare le numero de sequence attendu au numero de sequence dans le paquet
                #Si egalité on transmet le msg
                #Sinon on ne fait rien et on décrementer u[1]
                if(u[0]==host_port and u[1]==NumSeq): 
            
                    sourceMsgChat=self.serverProxy.getUserByAddress(host_port)
                    paquetARetransmettre=reception[2]
                    print("le paquet a retransmettre aux autres utilisateurs est:",paquetARetransmettre)
                    z=0
                    for u in self.serverProxy.getUserList() : 
                        #Si l'emetteur du msg est dans la meme room qu'un user, on envoie le msg à ce dernier
                        if(u.userChatRoom == sourceMsgChat.userChatRoom):
                            if(u.userName!=sourceMsgChat.userName): 
                                z+=1
                                print("//////////////////////////////////////////",z)
                                print("on envoie a:",u.userName)
                                seqTypAcq= (self.monNumeroSequence<< 4) | 9 
                                bufserver= struct.pack('!hh',4,seqTypAcq)
                                bufserver+=paquetARetransmettre
                                self.transport.write(bufserver,(host_port[0],host_port[1]))
                                self.filattente.append([self.monNumeroSequence,1,0,bufserver,u.userAddress])
                                print("le paquet de chat y compris l'entete est",bufserver)                         
                                self.monNumeroSequence=self.incrementerNumeroSequence(self.monNumeroSequence)
                                reactor.callLater(1,self.send_And_Wait,u.userAddress)
                
                elif(u[0]==host_port):
                    u[1]-=1
            
        pass
    