import blockchain
import pickle

#Server ID
SERVER_ID = "Server0001"

#function to save block into file
def saveObject(obj, filename):
        with open(filename, 'wb')as output:
            pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

genesisBlock = blockchain.create_genesis_block(SERVER_ID)
saveObject(genesisBlock, 'genesisBlock.pk1')
