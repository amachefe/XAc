from bitcoinrpc.authproxy import AuthServiceProxy
import csv

access = AuthServiceProxy("http://rpcusername:rpcpassword@127.0.0.1:8332")

number = 50
csvfile = open('addresses.csv','a')
writer = csv.writer(csvfile)

while number != 0:
    try:
        newaddress = access.getnewaddress()
        writer.writerow([newaddress])
        print(number)
        number -= 1
    except:
        pass

csvfile.close()
