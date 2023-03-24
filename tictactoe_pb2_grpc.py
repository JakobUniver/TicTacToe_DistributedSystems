# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import tictactoe_pb2 as tictactoe__pb2


class DateTimeServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetDateTime = channel.unary_unary(
                '/DateTimeService/GetDateTime',
                request_serializer=tictactoe__pb2.DateTimeRequest.SerializeToString,
                response_deserializer=tictactoe__pb2.DateTimeResponse.FromString,
                )


class DateTimeServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetDateTime(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DateTimeServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetDateTime': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDateTime,
                    request_deserializer=tictactoe__pb2.DateTimeRequest.FromString,
                    response_serializer=tictactoe__pb2.DateTimeResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'DateTimeService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class DateTimeService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetDateTime(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/DateTimeService/GetDateTime',
            tictactoe__pb2.DateTimeRequest.SerializeToString,
            tictactoe__pb2.DateTimeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class ReadyServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ServerReady = channel.unary_unary(
                '/ReadyService/ServerReady',
                request_serializer=tictactoe__pb2.ReadyRequest.SerializeToString,
                response_deserializer=tictactoe__pb2.ReadyResponse.FromString,
                )


class ReadyServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ServerReady(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ReadyServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ServerReady': grpc.unary_unary_rpc_method_handler(
                    servicer.ServerReady,
                    request_deserializer=tictactoe__pb2.ReadyRequest.FromString,
                    response_serializer=tictactoe__pb2.ReadyResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'ReadyService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ReadyService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ServerReady(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/ReadyService/ServerReady',
            tictactoe__pb2.ReadyRequest.SerializeToString,
            tictactoe__pb2.ReadyResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
