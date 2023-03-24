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
        request = tictactoe_pb2.DateTimeRequest()
        response = self.stub.GetDateTime(request)
        return response.date_time


class DateTimeServicer(tictactoe_pb2_grpc.DateTimeServiceServicer):
    def GetDateTime(self, request, context):
        current_time = datetime.datetime.utcnow()
        response = tictactoe_pb2.DateTimeResponse()
        response.date_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
        return response


def update_clock(client):  # Christian's algorithm for now
    start_time = time.time()
    server_time = datetime.datetime.strptime(client.get_datetime(), "%Y-%m-%d %H:%M:%S.%fZ")
    end_time = time.time()

    client_time = datetime.datetime.utcnow()
    estimated_server_time = server_time + datetime.timedelta(seconds=(end_time - start_time) / 2)
    time_diff = estimated_server_time - client_time

    print("Client time: ", client_time)
    # print("Estimated server time: ", estimated_server_time)
    print("Time diff with server: ", abs(time_diff))
    return estimated_server_time


def sync_time():
    pass


time_synced = False
def servers_ready():
    global time_synced, ports
    while True:
        try:
            for port in ports:
                with grpc.insecure_channel(f'localhost:{port}') as channel1:
                    client = ReadyClient(channel1)
                    response = client.server_ready()
            if not time_synced:
                time_synced = True
            break
        except grpc.RpcError as e:
            print("Trying to contact peers again!")
    return


def game_loop():
    print("Contacting peers!")
    servers_ready()
    print("All clients online!")
    lmao = input("Continue")


ports = ["20048", "20049", "20050"]
if __name__ == "__main__":
    server = grpc.server(ThreadPoolExecutor(max_workers=5))
    while True:
        try:
            port = input("Insert server port: ")
            server.add_insecure_port("[::]:" + port)
            ports.remove(port)
            break
        except:
            print("This port is taken, try again:")
    tictactoe_pb2_grpc.add_DateTimeServiceServicer_to_server(DateTimeServicer(), server)
    tictactoe_pb2_grpc.add_ReadyServiceServicer_to_server(ReadyServicer(), server)
    server.start()
    print("Server CONNECTED to port " + port + "...")
    while True:
        game_loop()

    server.wait_for_termination()
