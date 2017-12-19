import blockchain
import pickle
import ast
#layout of what a voting station would do

#sample machine ID
machine_id = '1234'

block_to_add = None


#Machine will receive genesis_block from server so that all machines have the same genesis block
#In that case genesis_block = whatver server gives it 
genesis_block = blockchain.create_genesis_block()

#machine will then create its own local blockchain utilitzing the genesis block given
blockchain.create_new_chain(genesis_block)



# Voter will vote and data will be packaged into proposed block
proposed_data = [["Voter ID", "000001"], ["President", "Eric Schweitzer"], ["Senate", "Eric Schweitzer"], ["Mayor", "Eric Schweitzer"]]
block_to_add = blockchain.next_block(machine_id, proposed_data)

blockchain.chain.append(block_to_add)

print("First Block")
print("Machine ID: ", blockchain.chain[1].machine_id)
print("Time: ", blockchain.chain[1].timestamp)
print("Ballot: ", blockchain.chain[1].data)
print("Current Hash: ", blockchain.chain[1].hash)
print("Previous Hash: ", blockchain.chain[1].previous_hash, "\n")

message = str(block_to_add.machine_id) + '?' + str(block_to_add.timestamp) \
              + '?' + str(block_to_add.data) + '?' + str(block_to_add.hash) + '?' + str(block_to_add.previous_hash)
#print(message)

message = message.split("?")
##################################################
#Message is currently parsed into the following:
# [0] = Machine ID
# [1] = Time
# [2] = Ballot (entire ballot as string)
# [3] = Current Hash
# [4] = Previous Hash
##################################################


#The ballot is going to be turned into a list. Each item in the list is a tuple. You can verify it with the commented out code following....
id = message[0]
from datetime import datetime
time = datetime.strptime(message[1], '%Y-%m-%d %H:%M:%S.%f')
ballot = ast.literal_eval(message[2])
hash = message[3]
previousHash = message[4]


compare = blockchain.Block(id, time, ballot, previousHash)

print("compare Block")
print("Machine ID: ", compare.machine_id)
print("Time: ", compare.timestamp)
print("Ballot: ", compare.data)
print("Current Hash: ", compare.hash)
print("Previous Hash: ", compare.previous_hash, "\n")


#print(type(block_to_add.data))
