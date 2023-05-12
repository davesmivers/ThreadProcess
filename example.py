from threadProcess import ThreadProcess

class file_worker(ThreadProcess):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Initialize the ThreadProcess superclass

    def startup_handler(self, **startup_args):
        """
        Startup method overridden from ThreadProcess.
        Perform initialization tasks when the worker process/thread starts.

        Args:
            **kwargs: Additional keyword arguments passed during initialization.

        """
        filename, mode = startup_args['filename'], startup_args['mode']
        self.file = open(filename, mode)  # Open the file specified in the arguments with the given mode

    def request_handler(self, command, uuid, parameters={}):
        """
        Request handler method overridden from ThreadProcess.
        Process individual requests received by the worker process/thread.

        Args:
            command (str): The command to be executed.
            uuid (str): The unique identifier for the request.
            parameters (dict): Additional parameters for the request.

        Returns:
            The response parameters.

        """
        if command == 'write':
            message = parameters['message']
            self.file.writelines([message])  # Write the message to the file
        elif command == 'write_backwards':
            message_backwards = parameters['message'][::-1]
            self.file.writelines([message_backwards])  # Write the message backwards to the file
        elif command == 'readlines':
            return self.file.readlines()  # Read all lines from the file and return them as the response

    def cleanup_handler(self):
        """
        Cleanup method overridden from ThreadProcess.
        Perform cleanup tasks when the worker process/thread finishes.

        """
        self.file.close()  # Close the file

if __name__ == '__main__':
    # Create an instance of file_worker for writing
    file_writer = file_worker(filename='knockknock.txt', mode='a', runtype='thread')
    file_writer.request('write', {'message': 'knock knock'})  # Send a write request to write "knock knock" to the file
    file_writer.request('write_backwards', {'message': "who's there"})  # Send a write request to write "who's there" backwards to the file
    file_writer.quit(blocking=True)  # Send a quit request to the worker process/thread and wait until it is processed

    # Create an instance of file_worker for reading
    file_reader = file_worker(filename='knockknock.txt', mode='r', runtype="process")
    file_reader.request('readlines', {'message': 'knock knock'})  # Send a readlines request to read all lines from the file
    for line in file_reader.response(blocking=True).result:
        print(line)  # Print each line read from the file
    file_reader.quit()  # Send a quit request to the worker process/thread