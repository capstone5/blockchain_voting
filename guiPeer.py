'''
The header for each byte stream sent and received is of the following format:
XXXXXXXXXX YYYYY Z* A* BBBB C*

- X represents the 10 character id of the sender
- Y represents the 5 character key of the sender
- Z represents any number of characters representing the ip address of the sender
- A represents any number of characters representing the port number of the sender
- B represents the uppercase 4 character command
- C represents the any number of characters making up the message sent

MACHINE_ID-MACHINE_KEY-IP_ADDRESS-PORT_NUMBER-COMMAND-MESSAGE
'''
import sched, time
import socket
import threading
import blockchain
import pickle
import ast
import gui

#----------------------------------------------------------------------------------------------------------------------#
#----------------------------- These identifiers will be hard coded onto each machine ---------------------------------#
MACHINE_ID = "Machine002"
MACHINE_KEY = "23456"
LEADER = False

#MAX_NUMBER_OF PEERS = 10

HOST = "192.168.43.66"
SERVER_PORT = "999"
SERVER_MACHINE_ID = "Server0001"
SERVER_KEY = "10101"

IP_ADDRESS = socket.gethostbyname(socket.getfqdn())
PORT_NUMBER = "1000"

#-- This message header will be used to send every message for verification purposes --#
MESSAGE_HEADER = MACHINE_ID + "|" + MACHINE_KEY + "|" + IP_ADDRESS + "|" + PORT_NUMBER
#----------------------------------------------------------------------------------------------------------------------#
#------------------------------List of peer info and list of peer socket connections-----------------------------------#
peers = []
registered_peers = []
#---------------------------------------- Block Chain will replace this list ------------------------------------------#
block_chain = []
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------- Lock to prevent race conditions --------------------------------------------#
lock = threading.Lock()
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#------------------------------------------ Class for holding client info ---------------------------------------------#
class Peer_Info:
    #-- Constructor --#
    def __init__(self, machineID, privateKey, ipAddress, portNumber):
        self.machineID = machineID
        self.privateKey = privateKey
        self.ipAddress = ipAddress
        self.portNumber = portNumber

    def change_ip_address(self, ipAddress):
        self.ipAddress = ipAddress

    def change_port_number(self, portNumber):
        self.portNumber = portNumber
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------- Function to Save Blockchain File -------------------------------------------#
def saveBlockchain(obj, filename):
        with open(filename, 'wb')as output:
            pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#----------------- This function creates a server socket, binds it and returns the object -----------------------------#
def makeserversocket(portNumber, backlog=5):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #-- allows us to reuse socket immediately after it is closed --#
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    #-- binds to whatever IP Address the peer is assigne --#
    s.bind(("", int(portNumber)))
    s.listen(backlog)
    s.setblocking(0)

    print("binding peer server socket to port " + PORT_NUMBER)
    print("Listening for connections...")
    return s
#----------------------------------------------------------------------------------------------------------------------#
# --------------------------------------------- Authentication Function -----------------------------------------------#

'''Function takes the machineID and key that have been extracted from the parse_incoming_message function, and checks 
the list of peers to make sure the connecting peer is authorized to connect. If it is the function returns true, if not
returns false'''
#----------------------------------------------------------------------------------------------------------------------#
def verify_incoming_peer(connection, machineID, key, ip_address, port_number):

    found_match = False

    print("Machine login info is: " + machineID + " " + key + "" + ip_address + "" + port_number)
    # -------------------------------------------------------------------------------------------------------------#

    # -------------- Loop through list of clients and see if a match with login info is found -------------------#
    for x in peers:
        # -- Client's machine id and private key match so it is confirmed to connect --#
        if (x.machineID == machineID) and (x.privateKey == key):
            print("match found!")

            # -- Client's IP address does not match so we update it in the Client list --#
            if (x.ipAddress != ip_address):
                x.change_ip_address(ip_address)
                print("Updated IP Address: " + ip_address)
            # -- Client's port number does not match so we update it in the Client list --#
            if (x.portNumber != port_number):
                x.change_port_number(port_number)
                print("Updated Port Number: " + str(port_number))

            # -- Match found so update variable --#
            found_match = True
            break
    # ------------------------------------------------------------------------------------------------------------#
    # ------------------------------------------- Peer failed to connect to ----------------------------------------#
    if found_match is False:
        print("Peer failed to provide a valid machine name and/or key.")
        return False
    # -----------------------------------------------------------------------------------------------------------------#
    # -------------------------------------- Client successfully connected --------------------------------------------#
    else:
        already_exist = False

        # -- Add socket to list of connections --#
        for p in registered_peers:
            if p.machineID == machineID:
                p.ipAddress = ip_address
                p.portNumber = port_number

                already_exist = True
                break
        if already_exist is False:
            with lock:
                registered_peers.append(Peer_Info(machineID, key, ip_address, port_number))
                print("Added to list of registered peers.")

        return True
# ---------------------------------------------------------------------------------------------------------------------#
# ------------------------------------------------- Handle connection -------------------------------------------------#
def handle_incoming_peer(connection):

    incoming_message = connection.recv(2048)
    incoming_message = incoming_message.decode()

    machine_id, key, ip_address, port_number, command, message = incoming_message.split("|", 6)

    #machine_id, key, ip_address, port_number, command, message = parse_incoming_message(incoming_message)

    if verify_incoming_peer(connection, machine_id, key, ip_address, port_number):
        print("peer verified, command: " + command)

        incoming_command_handler(connection, ip_address, port_number, command, message)

    else:
        print("Unverified attempt to connect at: %s" %(connection))
        outgoing_message = MESSAGE_HEADER + "|" + "ERRO" + "|" + ""
        connection.send(outgoing_message.encode("utf-8"))
# ---------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
def handle_outgoing_peer(connection, command, message=""):

    outgoing_message = MESSAGE_HEADER + "|" + command + "|" + message
    connection.send(outgoing_message.encode("utf-8"))

    handle_incoming_peer(connection)
#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
# ------------------ Command Handler takes commands from peer and performs necessary operation ------------------------#

def incoming_command_handler(connection, ip_address, port_number, command, incoming_message):

    global registered_peers

    #------------------------------------------------------------#
	#-- used for populating the peer and registered peer lists --#
    machineID = ""
    key = ""
    ipAddress = ""
    port = ""
    #------------------------------------------------------------#

    outgoing_message = ""
    #------------------------------------------------------------------------------------------------------------------#
    # --------------------------------------- Peer receives list of peers info ----------------------------------------#
    if command == "PEER":

        message_length = len(incoming_message)

        index = 0
        while index < message_length:

            # -----------  MachineID ---------------#
            while incoming_message[index] != " ":
                machineID += incoming_message[index]
                index += 1
            #---------------------------------------#
            index += 1
            # --------------- Key ------------------#
            while incoming_message[index] != " ":
                key += incoming_message[index]
                index += 1
            #---------------------------------------#
            index += 1
            #------------- ipAddress ---------------#
            while incoming_message[index] != " ":
                ipAddress += incoming_message[index]
                index += 1
            #---------------------------------------#
            index += 1
            #------------ portNumber ---------------#
            while incoming_message[index] != " ":
                port += incoming_message[index]
                index += 1
            #---------------------------------------#
            index +=1
            # -- Add peer info to list of peers --#
            peers.append(Peer_Info(machineID, key, ipAddress, port))

            # -- clear each variable so it can be reused --#
            machineID = ""
            key = ""
            ipAddress = ""
            port = ""

    #------------------------------------------------------------------------------------------------------------------#
    # -------------------  Peer receives command to send copy of registered peer list ---------------------------------#
    elif command == "REGP":

        print("sending list of registered peers to %s " % (connection))

        outgoing_message = MESSAGE_HEADER + "|" + "REPL" + "|" + ""

        for x in registered_peers:
            outgoing_message += (str(x.machineID) + " " + str(x.privateKey) + " " + str(x.ipAddress) + " " + str(x.portNumber) + " ")

        print(outgoing_message)
        connection.send(outgoing_message.encode("utf-8"))
    #------------------------------------------------------------------------------------------------------------------#
    # -----------------------------------  Peer receive list of registered peers  -------------------------------------#
    elif command == "REPL":
        message_length = len(incoming_message)
        index = 0

        while index < message_length:

            # -------------- MachineID ----------------#
            while incoming_message[index] != " ":
                machineID += incoming_message[index]
                index += 1
            #------------------------------------------#
            index += 1
            #------------------ Key -------------------#
            while incoming_message[index] != " ":
                key += incoming_message[index]
                index += 1
            #------------------------------------------#
            index += 1
            #--------------- ipAddress ----------------#
            while incoming_message[index] != " ":
                ipAddress += incoming_message[index]
                index += 1
            #------------------------------------------#
            index += 1
            #--------------- portNumber ---------------#
            while incoming_message[index] != " ":
                port += incoming_message[index]
                index += 1
            #------------------------------------------#
            index += 1

            #---- Add peer to list of registered peers if not already there ---#
            found = False
            for p in registered_peers:
                if (p.machineID == machineID) and (p.privateKey == key):
                    p.ipAddress = ipAddress
                    p.portNumber = port
                    found = True
                    break
            #------------------------------------------------------------------#
            if (found == False) and (machineID != MACHINE_ID):
                registered_peers.append(Peer_Info(machineID, key, ipAddress, port))

            # -- clear variables to reuse --#
            machineID = ""
            key = ""
            ipAddress = ""
            port = ""

    #---------------------------------------------------------------------------------------------------------------#
    #------------ Peer receive request from another node to join it's list of registered peers ---------------------#
    elif command == "JOIN":
        outgoing_message = MESSAGE_HEADER + "|" + "WELC" + "|" + incoming_message
        print(outgoing_message)
        connection.send(outgoing_message.encode("utf-8"))
    #---------------------------------------------------------------------------------------------------------------#
    #------------ Peer receives confirmation that it has joined list of registered peers for node ------------------#
    elif command == "WELC":
        print("Succesfully joined list of registered peers for node at ip address: %s port number: %s" %(ip_address, port_number))
    #---------------------------------------------------------------------------------------------------------------#
    #----------------------------- Peer receives command to update it's blockchain ---------------------------------#
    elif command == "ADDB":

        print("Adding block to blockchain, sent from peer: %s " % (connection))
        #parse the incoming_message to repackage into identical block
        parsedMessage = incoming_message.split("%")
        incomingId = parsedMessage[0]
        from datetime import datetime
        incomingTime = datetime.strptime(parsedMessage[1], '%Y-%m-%d %H:%M:%S.%f')
        incomingBallot = ast.literal_eval(parsedMessage[2])
        incomingPrevHash = parsedMessage[4]
        blockToAdd = blockchain.Block(incomingId, incomingTime, incomingBallot, incomingPrevHash)
        index = len(blockchain.chain)
        if (blockToAdd.previous_hash == blockchain.chain[index - 1].hash):
            blockchain.append_block(blockToAdd)
            saveBlockchain(blockchain.chain, 'localBlockchain.pk1')
        else:
            print("invalid block")
        
        outgoing_message = MESSAGE_HEADER + "|" + "CONF" + "|" + incoming_message
        print(outgoing_message)
        connection.send(outgoing_message.encode("utf-8"))
    #---------------------------------------------------------------------------------------------------------------#
    #-------- Peer reveives confirmation that other peer has received new block and added it to blockchain ---------#

    elif command == "CONF":
        print("Confirmation to add block to blockchain")

        block_chain.append(incoming_message)
        print("Block added: " + incoming_message)
    # --------------------------------------------------------------------------------------------------------------#
	#------------ Peer receives error message indicating something went wrong durring communication ----------------#
    elif command == "ERRO":
        print("error performing operation %s" %(ip_address))
    #---------------------------------------------------------------------------------------------------------------#
    # ------------------------------------------ Peer quits network -------------------------------------------------#
    elif command == "QUIT":
        outgoing_message = MESSAGE_HEADER + "|" + "DONE" + "|" + incoming_message
        connection.send(outgoing_message.encode("utf-8"))

        for i, p in enumerate(registered_peers):
            if (p.ipAddress == ipAddress) and (p.portNumber == port_number):
                print("Peer: %s signed off from network." %(p.machineID))
                del registered_peers[i]
    # -----------------------------------------------------------------------------------------------------------------#
    #------------------ Peer receives confirmation that it has disconnected from other peer ---------------------------#
    elif command == "DONE":
        print("Confirmed disconnection from peer")
    #------------------------------------------------------------------------------------------------------------------#
    elif command == "LEAD":
        global LEADER
        LEADER = True
        print("%s is now the leader" %(MACHINE_ID))

        time.sleep(10.0)
        LEADER = False
    #----------------------------- Peer receives unrecognized command to close socket ------------------------------#
    else:
        outgoing_message = MESSAGE_HEADER + "|" + "ERRO" + "|" + incoming_message

        print(outgoing_message)
        connection.send(outgoing_message.encode("utf-8"))
    #---------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------------------------------#
#-------------------------------------------- Outgoing command handler ------------------------------------------------#
def outgoing_command_handler(command, message):

    global registered_peers

    if command == "ADDB":
        for i,p in enumerate(registered_peers):
            sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # -- allows us to reuse socket immediately after it is closed --#
            sending_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                sending_socket.connect((p.ipAddress, int(p.portNumber)))
                handle_outgoing_peer(sending_socket, command, message)
                sending_socket.close()

            except socket.error as e:
                print(str(e))
                del registered_peers[i]

        # ----------------------------------------------------------------------------------#
        # ---------------------------------- Quit Program ----------------------------------#
    elif command == "QUIT":
        for p in registered_peers:
            try:
                sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sending_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                sending_socket.connect((p.ipAddress, int(p.portNumber)))
                handle_outgoing_peer(sending_socket, command, message)
                sending_socket.close()

            except socket.error as e:
                print(str(e))
        # ----------------------------------------------------------------------------------#
    elif command == "LIST PEERS":
        list(peers)

    elif command == "LIST REGPEERS":
        list(registered_peers)
        # -------------------------- Invalid Command Given ---------------------------------#
    else:
        print("invalid command dummy!")
    # ----------------------------------------------------------------------------------#

#----------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------ List peer info ------------------------------------------------------#
def list(peer_list):
    if peer_list:
        for i in peer_list:
            print(i.machineID + " " + i.privateKey + " " + i.ipAddress + " " + i.portNumber)
    else:
        print("List is empty")
#----------------------------------------------------------------------------------------------------------------------#
#------------ Initilize Peer by connecting to server and requesting peer_info and registered_peer_info ----------------#
def start_peer():

    peers.clear()
    registered_peers.clear()

    # --------- add server info to list of peers to allow communication --------#
    peers.append(Peer_Info(SERVER_MACHINE_ID, str(SERVER_KEY), "", ""))
    #---------------------------------------------------------------------------#

    # ------------------- Connect with server and get peer info ------------------------#
    command = "INIT"
    message = ""
    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sending_socket.connect((HOST, int(SERVER_PORT)))
        handle_outgoing_peer(sending_socket, command, message)

    except socket.error as msg:
        print("Failed to connect to server. " + str(msg))

        host_manual = input("IP Address-> ")
        port_number_manual = input("Port Number-> ")

        try:
            sending_socket.connect((host_manual, int(port_number_manual)))
            handle_outgoing_peer(sending_socket, command, message)

        except socket.error as msg:
            print("Failed to connnect to server. " + str(msg))

        finally:
            sending_socket.close()
    # ----------------------------------------------------------------------------------#

    # ------------- Connect with server and get registered peer info -------------------#
    command = "REGP"
    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sending_socket.connect((HOST, int(SERVER_PORT)))
        handle_outgoing_peer(sending_socket, command, message)

    except socket.error as msg:
        print("Failed to connect to server. " + str(msg))
        host_manual = input("IP Address-> ")
        port_number_manual = input("Port Number-> ")

        try:
            sending_socket.connect((host_manual, int(port_number_manual)))
            handle_outgoing_peer(sending_socket, command, message)

        except socket.error as msg:
            print("Failed to connnect to server. " + str(msg))
    finally:
        sending_socket.close()
    #------------------------------------------------------------------------------------#

    #---- Broadcast to other nodes to let them know new peer has joined network ---------#
    command = "JOIN"

    for peer in registered_peers:
        try:
            sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            print("failed to create server socket")

        try:
            sending_socket.connect((peer.ipAddress, int(peer.portNumber)))
        except:
            print("failed to connect to %s %s %s" %(peer.machineID,peer.ipAddress,peer.portNumber))
        try:
            handle_outgoing_peer(sending_socket, command, message)
            sending_socket.close()
        except:
            print("failed to handle outgoing peer")

#----------------------------------------------------------------------------------------------------------------------#
#----------------------------------------- Loop to Listen for connections ---------------------------------------------#
def listen_loop(server_socket):

    while True:
        try:
            peer, address = server_socket.accept()
            print("Connection from: %s" % (peer))

            #handle_incoming_peer(peer)

            # -- Create new thread to handle verification function --#
            t = threading.Thread(target=handle_incoming_peer, args=(peer,))
            t.daemon = True
            t.start()

        except:
            pass

    server_socket.close()

def broadcast():
    while True:
        if (LEADER) and (gui.ballotQueue.empty() != True):
            index = len(blockchain.chain)
            queuedData = gui.ballotQueue.get_nowait()
            blockToAdd = blockchain.next_block(MACHINE_ID, queuedData)
            if (blockToAdd.previous_hash == blockchain.chain[index - 1].hash):
                blockchain.append_block(blockToAdd)
                saveBlockchain(blockchain.chain, 'localBlockchain.pk1')
            message = (str)(blockToAdd.machine_id) + '%' + (str)(blockToAdd.timestamp) + '%' + (str)(blockToAdd.data) + '%' + (str)(blockToAdd.hash) + '%' + (str)(blockToAdd.previous_hash) 
            outgoing_command_handler('ADDB', message)

#----------------------------------------------------------------------------------------------------------------------#
#----------------------- Loop to take in votes, then request to update the blockchain ---------------------------------#
def MAIN():

    start_peer()

    server_socket = makeserversocket(int(PORT_NUMBER))

    t = threading.Thread(target=listen_loop, args=(server_socket,))
    t.daemon = True
    t.start()

    b = threading.Thread(target=broadcast,)
    b.daemon = True
    b.start()

    #----------------------------- Loop keeps running as long as peer is active ---------------------------------------#
    # -----------------------------------------------------------------------------------------------------------------#
    # -------------------------------------------------GUI-------------------------------------------------------------#

    gui.makeGUI()

    # ---------- Send Quit Message ---------- #
    outgoing_command_handler('QUIT', '')

MAIN()
