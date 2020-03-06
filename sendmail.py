import argparse
import socket

parser = argparse.ArgumentParser(description="Send mail over smtp")
parser.add_argument("subject", help="A subject for the message")
parser.add_argument("filename", help="Name of the file that contains the message to send")
parser.add_argument("sender", help="Email address of sender")
parser.add_argument("--recipient", help="Email address of recipient")
parser.add_argument("--server", help="SMTP server that will dispatch the message",
                    default="fafnir.cs.unc.edu")
parser.add_argument("--addrfile", help="A file containing email addresses for a mass-email. One address per line")
parser.add_argument("--debug", action="store_true")

args = parser.parse_args()

if not args.recipient and not args.addrfile:
    print("Either recipient or addrfile required")
    exit(1)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10.0)

if args.addrfile:
    with open(args.addrfile) as f:
        addresses = list(map(lambda x: x.strip(), f.readlines()))
else:
    addresses = [args.recipient]

with open(args.filename) as f:
    msg = f.read()
    msg.replace(".\n",". \n")
    n = len(msg)

def abort(s):
    sock.close()
    print("Error: %s -- Exiting" % s)
    exit(1)

def send_and_ack(s,code):
    sock.sendall(s)
    rcpt = sock.recv(4096)
    if(args.debug):
      print(rcpt)
    if not rcpt[:3] == str(code):
        abort("Bad response from server")

try:
    sock.connect((args.server, 25)) 
    if sock.recv(4096)[:1] == "2":
        send_and_ack("HELO %s\n" % socket.gethostname(), 250)
    else:
        abort("Bad response from server")
    
    for recipient in addresses:
        send_and_ack("MAIL FROM:<%s>\n" % args.sender, 250)
        send_and_ack("RCPT TO:<%s>\n" % recipient, 250)
        send_and_ack("DATA\n", 354)
        
        sock.sendall("Subject: %s\n" % args.subject)
        sock.sendall(msg)
        
        tailfix = "" if msg[-1] == "\n" else "\n"
        send_and_ack(tailfix + ".\n", 250)
        
    sock.sendall("QUIT\n")
    sock.close()
    print("Message(s) sent!")

    

except (socket.error) as e:
    print("Socket error:")
    print(e)
