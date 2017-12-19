import blockchain
import pickle 

with open('localBlockchain.pk1', 'rb') as input:
    chain = pickle.load(input)



    
i = 0
    
while i < len(chain):
    print(i," Block")
    print("Machine ID: ", chain[i].machine_id)
    print("Time: ", chain[i].timestamp)
    print("Ballot: ", chain[i].data)
    print("Current Hash: ", chain[i].hash)
    print("Previous Hash: ", chain[i].previous_hash, "\n")
    i+=1
