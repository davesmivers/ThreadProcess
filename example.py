from threadProcess import ThreadProcess

class file_worker(ThreadProcess):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Initialize the ThreadProcess superclass

    def startup_handler(self, **startup_args):
        """
        Startup method overridden from ThreadProcess.
        Perfo   rm initialization tasks when the worker process/thread starts.

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
        if command == 'write_line':
            message = parameters['message']  + '\n'
            self.file.write(message)  # Write the message to the file
        elif command == 'write_line_backwards':
            message_backwards = parameters['message'][::-1] + '\n'
            self.file.write(message_backwards)  # Write the message backwards to the file
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
    file_writer = file_worker(filename='output.txt', mode='a', runtype='thread')

    # Send a write request to write "knock knock" to the file
    file_writer.request('write_line', {'message': 'knock knock'})
    response = file_writer.response(blocking=True)  # Get the last response
    print("1st response:")
    print(response.command, response.uuid, response.success)

    # Send a write request to write "who's there" backwards to the file
    file_writer.request('write_line_backwards', {'message': "who's there"}, respond=False)

    # Send a quit request to the worker process/thread and wait until it is processed
    file_writer.quit(blocking=True)

    # Create an instance of file_worker for reading
    file_reader = file_worker(filename='output.txt', mode='r', runtype="process")

    # Send a readlines request to read all lines from the file
    request_id_3 = file_reader.request('readlines', {'message': 'knock knock'})

    print("2nd response:")
    # Explicitly request request_id_3
    for line in file_reader.response(blocking=True, id=request_id_3).result:  
        print(line[:-1])  # Print each line read from the file

    # Send a quit request to the worker process/thread
    file_reader.quit()

