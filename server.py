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

    def set_datetime(self, time_diff):
        request = tictactoe_pb2.SetDateTimeRequest(time_diff)
        response = self.stub.SetDateTime(request)
        return response.success


class DateTimeService(tictactoe_pb2_grpc.DateTimeServiceServicer):
    def GetDateTime(self, request, context):
        current_time = time.time()
        response = tictactoe_pb2.GetDateTimeResponse(date_time=current_time)
        return response

    def SetDateTime(self, request, context):
        global time_synced
        avg_time = request.avg_time
        time_diff = datetime.datetime.fromtimestamp(time.time()) - datetime.datetime.fromtimestamp(avg_time)
        time_synced = True
        print(f"Time difference: {time_diff}")
        response = tictactoe_pb2.SetDateTimeResponse(success=True)
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
    times = [time.time()]
    for port in ports:
        with grpc.insecure_channel(f'localhost:{port}') as channel:
            #client = DateTimeClient(channel)
            #response = client.get_datetime()
            stub = tictactoe_pb2_grpc.DateTimeServiceStub(channel)
            response = stub.GetDateTime(tictactoe_pb2.GetDateTimeRequest())
            times.append(response.date_time)
    avg_times = [sum(times) / len(times) for t in times[1:]]
    for i in range(len(ports)):
        with grpc.insecure_channel(f'localhost:{ports[0]}') as channel:
            stub = tictactoe_pb2_grpc.DateTimeServiceStub(channel)
            response = stub.SetDateTime(tictactoe_pb2.SetDateTimeRequest(avg_time=avg_times[i]))
            print(response.success)
    return


time_synced = False


def servers_ready():
    global time_synced, ports
    while not time_synced:
        try:
            for port in ports:
                with grpc.insecure_channel(f'localhost:{port}') as channel:
                    client = ReadyClient(channel)
                    response = client.server_ready()
            time.sleep(1)
            if time_synced:
                break
            else:
                print("Start timesync")
                sync_time()
                time_synced = True
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
    tictactoe_pb2_grpc.add_ReadyServiceServicer_to_server(ReadyServicer(), server)
    tictactoe_pb2_grpc.add_DateTimeServiceServicer_to_server(DateTimeService(), server)
    server.start()
    print("Server CONNECTED to port " + port + "...")

    #while True:
    game_loop()

    print("End")
    server.wait_for_termination()
