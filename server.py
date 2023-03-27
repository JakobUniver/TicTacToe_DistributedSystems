import datetime
import time
from concurrent.futures import ThreadPoolExecutor

import grpc

import tictactoe_pb2
import tictactoe_pb2_grpc


COORDINATOR = None
PORTS = ["20048", "20049", "20050"]
MY_PORT = ''
MASTER_PORT = '20048'
PLAYER_PORTS = PORTS[:]
PLAYER_PORTS.remove(MASTER_PORT)
MY_ROLE = ''
TIME_SYNCED = False
BOARD = ['empty', 'empty', 'empty', 'empty', 'empty', 'empty', 'empty', 'empty', 'empty']

class ReadyClient:
    def __init__(self, channel):
        self.stub = tictactoe_pb2_grpc.ReadyServiceStub(channel)

    def server_ready(self):
        request = tictactoe_pb2.ReadyRequest()
        response = self.stub.ServerReady(request)
        return response.ready


class ReadyServicer(tictactoe_pb2_grpc.ReadyServiceServicer):
    def ServerReady(self, request, context):
        response = tictactoe_pb2.ReadyResponse()
        response.ready = 1
        return response


class DateTimeClient:
    def __init__(self, channel):
        self.stub = tictactoe_pb2_grpc.DateTimeServiceStub(channel)

    def get_datetime(self):
        request = tictactoe_pb2.GetDateTimeRequest()
        response = self.stub.GetDateTime(request)
        return response.date_time


class DateTimeService(tictactoe_pb2_grpc.DateTimeServiceServicer):
    def GetDateTime(self, request, context):
        current_time = time.time()
        response = tictactoe_pb2.GetDateTimeResponse(date_time=current_time)
        return response

    def SetDateTime(self, request, context):
        global TIME_SYNCED
        avg_time = request.avg_time
        time_diff = datetime.datetime.fromtimestamp(time.time()) - datetime.datetime.fromtimestamp(avg_time)
        TIME_SYNCED = True
        print(f"Time difference: {time_diff}")
        response = tictactoe_pb2.SetDateTimeResponse(success=True)
        return response


class GameClient:
    def __init__(self, channel):
        self.stub = tictactoe_pb2_grpc.GameServiceStub(channel)




class GameService(tictactoe_pb2_grpc.GameServiceServicer):
    def ListBoard(self, request, context):
        response = tictactoe_pb2.ListBoardResponse(board=BOARD)
        return response

    def SetSymbol(self, request, context):
        slot, symbol = request.symbols.split(',')
        slot = int(slot)
        if BOARD[slot-1] == 'empty':
            BOARD[slot-1] = f'{symbol}:{time.time()}'
            output = 'SUCCESS'
        else:
            output = 'FAIL'
        response = tictactoe_pb2.SetSymbolResponse(output=output)
        return response

    def SetTime(self, request, context):
        success = True
        response = tictactoe_pb2.SetTimeResponse(success=success)
        return response



class ElectionClient:
    def __init__(self, channel):
        self.stub = tictactoe_pb2_grpc.ElectionServiceStub(channel)

    def send_election(self, sender_id, election_id):
        request = tictactoe_pb2.ElectionRequest()
        request.sender_id = sender_id
        request.election_id = election_id
        response = self.stub.SendElection(request)
        return response

class ElectionServicer(tictactoe_pb2_grpc.ElectionServiceServicer):
    def SendElection(self, request, context):
        print(f"Received election message from process {request.sender_id} with election ID {request.election_id}")
        result = tictactoe_pb2.ElectionResponse()
        result.success = True
        return result

class CoordinatorClient:
    def __init__(self, channel):
        self.stub = tictactoe_pb2_grpc.CoordinatorServiceStub(channel)

    def coordinator_elected(self, leader):
        request = tictactoe_pb2.CoordinatorRequest()
        request.leader_port = leader
        response = self.stub.CoordinatorElected(request)
        return response


class CoordinatorServicer(tictactoe_pb2_grpc.CoordinatorServiceServicer):
    def CoordinatorElected(self, request, context):
        global COORDINATOR
        response = tictactoe_pb2.CoordinatorResponse()
        COORDINATOR = request.leader_port
        print(f"Elected coordinator is Node{PORTS.index(COORDINATOR)} (port {COORDINATOR})")
        response.success = True
        return response

class AssignSymbolClient:
    def __init__(self, channel):
        self.stub = tictactoe_pb2_grpc.AssignSymbolServiceStub(channel)

    def assign_symbol(self, symbol):
        request = tictactoe_pb2.AssignSymbolRequest()
        request.symbol = symbol
        response = self.stub.AssignSymbol(request)
        return response


class AssignSymbolServicer(tictactoe_pb2_grpc.AssignSymbolServiceServicer):
    def AssignSymbol(self, request, context):
        global MY_ROLE
        MY_ROLE = request.symbol
        response = tictactoe_pb2.AssignSymbolResponse()
        response.success = True
        return response

def election():
    global COORDINATOR
    if COORDINATOR != None:
        return
    num = PORTS.index(MY_PORT)
    successful = [0 for port in PORTS]

    for send in range(num + 1, len(PORTS) - 1):
        send_port = PORTS[send]
        print(num)
        print(send)
        print(send_port)
        print()
        try:
            with grpc.insecure_channel(f'localhost:{send_port}') as channel:
                client = ElectionClient(channel)
                response = client.send_election(num, len(PORTS) - 1)
                if response.success:
                    print(f"Successful election response from {send_port}")
                    successful[send] = 1
        except grpc.RpcError as e:
            print("Error with sending election messages!")
            print(e)
    print(successful)
    if sum(successful) == 0:
        COORDINATOR = MY_PORT
        for send_port in PORTS:
            if send_port == MY_PORT:
                continue
            try:
                with grpc.insecure_channel(f'localhost:{send_port}') as channel:
                    client = CoordinatorClient(channel)
                    response = client.coordinator_elected(MY_PORT)
                    if response.success:
                        print(f"Successful coordinator message to {send_port}")
            except grpc.RpcError as e:
                print("Error with sending coordinator messages!")
                print(e)

def servers_ready():
    global TIME_SYNCED, PORTS

    #### TIMESYNC
    while not TIME_SYNCED:
        try:
            for port in PORTS:
                with grpc.insecure_channel(f'localhost:{port}') as channel:
                    client = ReadyClient(channel)
                    response = client.server_ready()
            if TIME_SYNCED:
                break
            else:
                print("Start timesync")
                sync_time()
                TIME_SYNCED = True
        except grpc.RpcError as e:
            print("Trying to contact peers again!")
    return


def sync_time():
    times = [time.time()]
    for port in PORTS:
        with grpc.insecure_channel(f'localhost:{port}') as channel:
            stub = tictactoe_pb2_grpc.DateTimeServiceStub(channel)
            response = stub.GetDateTime(tictactoe_pb2.GetDateTimeRequest())
            times.append(response.date_time)
    avg_times = [sum(times) / len(times) for t in times[1:]]
    for i in range(len(PORTS)):
        with grpc.insecure_channel(f'localhost:{PORTS[0]}') as channel:
            stub = tictactoe_pb2_grpc.DateTimeServiceStub(channel)
            response = stub.SetDateTime(tictactoe_pb2.SetDateTimeRequest(avg_time=avg_times[i]))
            print(response.success)
    return


def list_board():
    with grpc.insecure_channel(f'localhost:{MASTER_PORT}') as channel:
        stub = tictactoe_pb2_grpc.GameServiceStub(channel)
        response = stub.ListBoard(tictactoe_pb2.ListBoardRequest())
        print(response.board)
    return


def set_symbol(symbols):
    with grpc.insecure_channel(f'localhost:{MASTER_PORT}') as channel:
        stub = tictactoe_pb2_grpc.GameServiceStub(channel)
        response = stub.SetSymbol(tictactoe_pb2.SetSymbolRequest(symbols=symbols[0]))
        if response.output == 'SUCCESS':
            print(response.output)
        elif response.output == 'FAIL':
            print("Move failed, try another slot")
    return response.output


def game_over():
    pass


def set_time(param):
    pass


def assignSymbols():
    with grpc.insecure_channel(f'localhost:{PORTS[0]}') as channel:
        client = AssignSymbolClient(channel)
        response = client.assign_symbol('PLAYER X')
        if response.success:
            print(f"Port {PORTS[0]} asssigned symbol X")
        else:
            print("Symbol assignment failed!")
    with grpc.insecure_channel(f'localhost:{PORTS[1]}') as channel:
        client = AssignSymbolClient(channel)
        response = client.assign_symbol('PLAYER O')
        if response.success:
            print(f"Port {PORTS[1]} asssigned symbol O")
        else:
            print("Symbol assignment failed!")
    return


def game_loop():
    global MY_PORT, MASTER_PORT, MY_ROLE
    print("Contacting peers!")
    servers_ready()
    print("All clients online!")

    time.sleep(3)

    PORTS.append(MY_PORT)
    PORTS.sort()
    election()
    PORTS.remove(MY_PORT)

    if MY_PORT == COORDINATOR:
        MY_ROLE = 'MASTER'
        assignSymbols()
    # elif MY_PORT == '20049':
    #     MY_ROLE = 'PLAYER X'
    # elif MY_PORT == '20050':
    #     MY_ROLE = 'PLAYER O'

    time.sleep(3)
    while True:
        args = input(f"{MY_ROLE}> ").split(' ')
        command = args[0]
        if command == "Set-symbol" and MY_ROLE != 'MASTER':
            output = set_symbol(args[1:])
            if output == "GAMEOVER":
                game_over()
                break
        elif command == "List-board":
            list_board()
        elif command == "Set-node-time":
            set_time(args[1:])
        else:
            print("Command not available, try again")

    print("Resetting the game in 5 seconds")
    time.sleep(5)
    game_loop()


if __name__ == "__main__":
    server = grpc.server(ThreadPoolExecutor(max_workers=5))
    while True:
        try:
            port = input("Insert server port: ")
            server.add_insecure_port("[::]:" + port)
            PORTS.remove(port)
            MY_PORT = port
            break
        except:
            print("This port is taken, try again:")
    tictactoe_pb2_grpc.add_ReadyServiceServicer_to_server(ReadyServicer(), server)
    tictactoe_pb2_grpc.add_DateTimeServiceServicer_to_server(DateTimeService(), server)
    tictactoe_pb2_grpc.add_GameServiceServicer_to_server(GameService(), server)
    tictactoe_pb2_grpc.add_ElectionServiceServicer_to_server(ElectionServicer(), server)
    tictactoe_pb2_grpc.add_CoordinatorServiceServicer_to_server(CoordinatorServicer(), server)
    tictactoe_pb2_grpc.add_AssignSymbolServiceServicer_to_server(AssignSymbolServicer(), server)
    server.start()
    print("Server CONNECTED to port " + port + "...")

    game_loop()

    print("End")
    server.wait_for_termination()
