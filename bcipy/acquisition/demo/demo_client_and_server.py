# pylint: disable=fixme
"""Demo script demonstrating both the acquisition server and client."""


def main():
    """Creates a sample client that reads data from a sample TCP server
    (see demo/server.py). Data is written to a rawdata.csv file, as well as a
    buffer.db sqlite3 database. These files are written in whichever directory
    the script was run.

    The client/server can be stopped with a Keyboard Interrupt (Ctl-C)."""

    import time
    import sys

    # Allow the script to be run from the bci root, acquisition dir, or
    # demo dir.
    sys.path.append('.')
    sys.path.append('..')
    sys.path.append('../..')

    from bcipy.acquisition.datastream.generator import random_data_generator, generator_factory
    from bcipy.acquisition.protocols import registry
    from bcipy.acquisition.client import DataAcquisitionClient
    from bcipy.acquisition.datastream.tcp_server import TcpDataServer

    host = '127.0.0.1'
    port = 9000
    # The Protocol is for mocking data.
    protocol = registry.default_protocol('DSI')
    server = TcpDataServer(
        protocol=protocol,
        generator=generator_factory(random_data_generator, channel_count=len(protocol.channels)),
        host=host,
        port=port)

    # Device is for reading data.
    # pylint: disable=invalid-name
    Device = registry.find_device('DSI')
    dsi_device = Device(connection_params={'host': host, 'port': port})
    raw_data_name = 'demo_raw_data.csv'
    client = DataAcquisitionClient(device=dsi_device, raw_data_file_name=raw_data_name)

    try:
        server.start()
        client.start_acquisition()

        print("\nCollecting data for 10s... (Interrupt [Ctl-C] to stop)\n")

        while True:
            time.sleep(10)
            client.stop_acquisition()
            client.cleanup()
            print("Number of samples: {0}".format(client.get_data_len()))
            server.stop()
            print(f"The collected data has been written to {raw_data_name}")
            break

    except KeyboardInterrupt:
        print("Keyboard Interrupt; stopping.")
        client.stop_acquisition()
        client.cleanup()
        print("Number of samples: {0}".format(client.get_data_len()))
        server.stop()
        print(f"The collected data has been written to {raw_data_name}")


if __name__ == '__main__':
    main()
