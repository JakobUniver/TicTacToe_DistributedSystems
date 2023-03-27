import datetime
import time
from concurrent.futures import ThreadPoolExecutor

import grpc

import tictactoe_pb2
import tictactoe_pb2_grpc


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


BOARD = ['empty', 'empty', 'empty', 'empty', 'empty', 'empty', 'empty', 'empty', 'empty']


class GameService(tictactoe_pb2_grpc.GameServiceServicer):
    def ListBoard(self, request, context):
        response = tictactoe_pb2.ListBoardResponse(board=BOARD)
        return response

    def SetSymbol(self, request, context):
        output = ''
        response = tictactoe_pb2.SetSymbolResponse(output=output)
        return response

    def SetTime(self, request, context):
        success = True
        response = tictactoe_pb2.SetTimeResponse(success=success)
        return response


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


TIME_SYNCED = False


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


def list_board():
    with grpc.insecure_channel(f'localhost:{MASTER_PORT}') as channel:
        stub = tictactoe_pb2_grpc.GameServiceStub(channel)
        response = stub.ListBoard(tictactoe_pb2.ListBoardRequest())
        print(response.board)
    return


def set_symbol(param):
    return ''


def set_time(param):
    pass


PORTS = ["20048", "20049", "20050"]
MY_PORT = ''
MASTER_PORT = '20048'
PLAYER_PORTS = PORTS[:]
PLAYER_PORTS.remove(MASTER_PORT)
MY_ROLE = ''


def game_over():
    pass


def game_loop():
    global MY_PORT, MASTER_PORT, MY_ROLE
    print("Contacting peers!")
    servers_ready()
    print("All clients online!")

    #TODO LEADER ELECTION
    ## Dummy leader election
    if MY_PORT == '20048':
        MY_ROLE = 'LEADER'
    elif MY_PORT == '20049':
        MY_ROLE = 'PLAYER 1'
    elif MY_PORT == '20050':
        MY_ROLE = 'PLAYER 2'

    time.sleep(0.5)
    while True:
        args = input(f"{MY_ROLE}> ").split(' ')
        command = args[0]
        if command == "Set-symbol":
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
    server.start()
    print("Server CONNECTED to port " + port + "...")

    game_loop()

    print("End")
    server.wait_for_termination()
