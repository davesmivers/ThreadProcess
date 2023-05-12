import threading  # Provides support for multi-threading in Python
import multiprocessing  # Provides support for multi-processing in Python
import queue  # Provides the Queue class for thread-safe communication between threads/processes
import traceback  # Provides utilities for printing stack traces and exception information
import time  # Provides functions for working with time and timing operations
import uuid  # Provides functionality for generating and working with universally unique identifiers (UUIDs)


class ThreadProcess():
    """
    A generic handler for long-running threads and processes.

    This class provides a framework for executing and managing long-running threads or processes.
    It handles the communication between the main process/thread and the worker process/thread.
    Requests are sent to the worker process/thread via a request queue, and responses are received
    through a response queue.

    Usage:
    1. Create an instance of the ThreadProcess class, specifying the desired execution mode ('thread'
       or 'process') and any additional arguments needed by the main process/thread.
    2. The main process/thread is started automatically upon initialization.
    3. Send requests to the worker process/thread by calling the `request()` method.
    4. Retrieve the responses from the worker process/thread by calling the `response()` method.

    Request Format:
    - All requests should be dictionaries with the following keys:
        - 'command': The command to be executed by the worker process/thread.
        - 'uuid': A unique identifier for the request.
        - 'respond': A flag indicating whether a response is expected for the request.
        - Additional keys can be included for command-specific parameters.

    Note:
    - All requests should return a response. If a request does not result in a response, the request
      will be echoed back as the response.
    - If the 'command' value is 'quit', the worker thread/process will terminate.
    - Exceptions during startup, the main loop, or cleanup are caught and logged with relevant error
      messages, allowing the program to continue executing.

    Attributes:
        requestQ (Queue): The queue for sending requests to the worker process/thread.
        responseQ (Queue): The queue for receiving responses from the worker process/thread.
        worker (Thread or Process): The worker process/thread handling the main process.
        status (str): The current status of the ThreadProcess instance.
        sleep_time (float): Time to sleep if there were no requests.

    Methods:
        main(args): The main process/thread function that should be overridden in subclasses. It
                    handles the main logic of the process/thread execution.
        request_handler(command, uuid, parameters): Placeholder method for processing individual requests.
                                                     It should be overridden in subclasses to provide
                                                     specific request processing functionality.
        startup(**kwargs): Placeholder method for performing startup tasks. It should be overridden
                           in subclasses to provide specific startup functionality.
        cleanup(): Placeholder method for performing cleanup tasks. It should be overridden in
                   subclasses to provide specific cleanup functionality.
        request(command, parameters={}, respond=True): Sends a request to the worker process/thread.
        response(timeout=None): Retrieves a response from the worker process/thread.
        quit(blocking=True): Sends a quit request to the worker process/thread and optionally waits
                             until the quit request is processed.

    """

    def request_handler(self, command, uuid, parameters):
        """
        Placeholder method for processing individual requests.

        Args:
            command (str): The command to be processed.
            uuid (str): The unique identifier for the request.
            parameters (dict): Additional parameters for the request.

        Returns:
            The response parameters.

        """
        response_params = None  # Placeholder for response parameters
        return response_params
    
    def startup_handler(self, **startup_args):
        """
        Placeholder method for performing startup tasks.

        """
        pass

    def cleanup_handler(self):
        """
        Placeholder method for performing cleanup tasks.

        """
        pass

    def __init__(self, runtype='thread', sleep_time=0.02, **startup_args):
        """
        Initializes the ThreadProcess object.

        Args:
            args: Additional arguments needed for the main process.
            type (str): The type of execution ('thread' or 'process').
            sleep_time (float): Time to sleep if there were no requests.
        """
        self.status = 'init'
        self.sleep_time = sleep_time

        if runtype == 'thread':
            self.requestQ = queue.Queue()
            self.responseQ = queue.Queue()
            self.worker = threading.Thread(target=self.main, args=(startup_args,))
        elif runtype == 'process':
            self.requestQ = multiprocessing.Queue()
            self.responseQ = multiprocessing.Queue()
            self.worker = multiprocessing.Process(target=self.main, args=(startup_args,))
        else:
            raise ValueError("Invalid execution type. Must be 'thread' or 'process'.")

        self.worker.start()
        self.status = 'starting'
        self.status = self.responseQ.get()
    

    def main(self, startup_args):
        """
        The main process of the ThreadProcess class.

        Args:
            startup_args (dict): Additional arguments needed for the startup process.

        """
        try:
            self.startup_handler(**startup_args)
            self.responseQ.put('started')
        except Exception as e:
            """
            Exception handling for startup errors.
            Prints the error message and sets the status to 'startup_error'.
            """
            print("Error in startup of ThreadProcess:", id(self.worker))
            traceback.print_exc()
            self.status = 'startup_error'

        if self.status != 'startup_error':
            while True:
                if not self.requestQ.empty():
                    self.status = 'processing'
                    request = self.requestQ.get()
                    command, uuid, respond = request['command'], request['uuid'], request['respond']
                    parameters = {key: value for key, value in request.items()
                                if key not in ['command', 'uuid', 'respond']}
                    if command == 'quit':
                        self.status = 'quitting'
                        break
                    else:
                        response_params = None
                        success = False
                        try:
                            response_params = self.request_handler(command, uuid, parameters)
                            success = True
                        except  Exception as e:
                            """
                            Exception handling for errors in the request handler.
                            """
                            print("Error in main loop of ThreadProcess:", id(self.worker))
                            traceback.print_exc()

                        if respond:
                            response = {'command': command, 'uuid': uuid}
                            response['success'] = success
                            response['parameters'] = response_params
                            self.responseQ.put(response)
                else:
                    self.status = 'running'
                    time.sleep(self.sleep_time)

        try:
            self.cleanup_handler()
            if request['command'] == 'quit' and respond:
                response = request
                request['parameters'] = None
                request['success'] = True
                self.responseQ.put(request)
            self.status = 'finished'
        except Exception as e:
            """
            Exception handling for cleanup errors.
            Prints the error message.
            """
            print("Error in cleanup of ThreadProcess:", id(self.worker))
            traceback.print_exc()

    
    def request(self, command, parameters={}, respond=True):
        """
        Sends a request to the worker process/thread.

        Args:
            command (str): The command to be executed.
            parameters (dict): Additional parameters for the request.
            respond (bool): Flag indicating whether a response is expected for the request.

        Returns:
            str: The unique identifier (UUID) of the request.

        """
        request = parameters
        request.update({'command': command, 'respond': respond})
        request['uuid'] = str(uuid.uuid1())
        self.requestQ.put(request)
        return request['uuid']

    def response(self, timeout=0, blocking=False):
        """
        Retrieves a response from the worker process/thread.

        Args:
            timeout (float): The maximum time to wait for a response in seconds.

        Returns:
            tuple or None:
            Returns a tuple containing the command, UUID, success flag, 
            and response parameters of the retrieved response. 
            If no response is available within the specified timeout, it returns None.
        """
        if blocking: timeout = 1E5

        if timeout > 0 or not self.responseQ.empty():
            try:
                response = self.responseQ.get(timeout=timeout)
                return response['command'], response['uuid'], response['success'], response['parameters']
            except queue.Empty:
                return None

    def quit(self, blocking=True):
        """
        Sends a quit request to the worker process/thread and optionally waits until the quit request is processed.

        Args:
            blocking (bool): Flag indicating whether to wait for the quit request to be processed.

        """
        id = self.request('quit', respond=True)
        while blocking:
            response = self.response(blocking=True)
            if response[1] == id: break