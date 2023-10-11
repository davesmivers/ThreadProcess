import threading  # Provides support for multi-threading in Python
import multiprocessing  # Provides support for multi-processing in Python
import queue  # Provides the Queue class for thread-safe communication between threads/processes
import traceback  # Provides utilities for printing stack traces and exception information
import time  # Provides functions for working with time and timing operations
import uuid  # Provides functionality for generating and working with universally unique identifiers (UUIDs)
import os # Provides functions for interacting with the operating system

class ThreadProcess:
    """
    ThreadProcess: Asynchronous Execution Wrapper

    Description:
    A wrapper for executing tasks in either a separate thread or process.
    It provides a uniform interface for sending requests and receiving responses
    between the main application and the thread/process.

    Usage:
    1. Create an instance of the class.
    2. Send requests using the `request` method.
    3. Retrieve responses using the `response` method.

    Request Format:
    ---------------
    Requests should follow this dictionary format:
    - 'command': The action for the worker process/thread to execute.
    - 'uuid': A unique identifier for that request.
    - 'respond': A flag indicating if the request expects a response.
    - Additional keys can be added  to a 'parameters' dict for command-specific arguments.

    Notes:
    - Each request is identified by a UUID.
    - The response will also carry the same UUID for identification.
    - The request can optionally request a response.
    - The response can be fetched at any time after the request.

    Methods:
    - __init__: Initializes the ThreadProcess object.
    - request_handler: Placeholder method for processing individual requests.
    - startup_handler: Placeholder method for performing startup tasks.
    - cleanup_handler: Placeholder method for performing cleanup tasks.
    - main: The main process of the ThreadProcess class.
    - pre_request_function: Placeholder method for monitoring events.
    - no_request_function: Placeholder method for handling no requests.
    - post_request_function: Placeholder method for handling post-request tasks.
    - request: Sends a request to the worker process/thread.
    - response: Retrieves a response from the worker process/thread.
    - quit: Sends a quit request to the worker process/thread.
    - _maintain_loop_time: Maintains the loop time by sleeping if necessary.
    - _response: A helper class representing a response object.

    Attributes:
    - worker_status: Status of the worker thread/process.
    - target_loop_period: Target loop duration for the worker.
    - requestQ: Queue for placing requests.
    - responseQ: Queue for fetching responses.
    - worker: Thread or Process instance.
    - response_lock: Lock for managing concurrent access to the response queue.
    ... and others ...
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

    def __init__(self, runtype='thread', target_loop_period=0.001, **startup_args):
        """
        Initializes the ThreadProcess object.

        Args:
            args: Additional arguments needed for the main process.
            type (str): The type of execution ('thread' or 'process').
            loop_time (float): Time to sleep if there were no requests.
        """
        self.worker_status = 'init'
        self.target_loop_period = target_loop_period

        if runtype == 'thread':
            self.requestQ = queue.Queue()
            self.responseQ = queue.Queue()
            self.worker = threading.Thread(target=self.main, args=(startup_args,))
            self.response_lock = threading.Lock()
        elif runtype == 'process':
            self.requestQ = multiprocessing.Queue()
            self.responseQ = multiprocessing.Queue()
            self.worker = multiprocessing.Process(target=self.main, args=(startup_args,))
            self.response_lock = multiprocessing.Lock()
        else:
            raise ValueError("Invalid execution type. Must be 'thread' or 'process'.")
        
        self.worker_status = 'starting'
        self.worker.start()
        self.worker_status = self.responseQ.get()
        self.master_status = 'running'
    

    def main(self, startup_args):
        """
        The main process of the ThreadProcess class.

        Args:
            startup_args (dict): Additional arguments needed for the startup process.

        """
        try:
            self.startup_handler(**startup_args)
            with self.response_lock: self.responseQ.put('started')
            command, respond = None, False
        except Exception as e:
            """
            Exception handling for startup errors.
            Prints the error message and sets the status to 'startup_error'.
            """
            print("Error in startup of ThreadProcess:", id(self.worker))
            traceback.print_exc()
            self.worker_status = 'startup_error'
            with self.response_lock: self.responseQ.put('startup_error')
            command, respond = 'quit', False
        if self.worker_status != 'startup_error':
            self.last_loop_time = time.time()
            self.loop_iteration = 0
            main_thread = threading.main_thread()
            while main_thread.is_alive():
                self.loop_iteration += 1
                # Call a generic pre-request function to perform any monitoring/logging/etc.
                self.pre_request_function()
                # Check for requests and process them if available
                if not self.requestQ.empty():
                    self.worker_status = 'processing'
                    request = self.requestQ.get()
                    command, uuid, respond = request['command'], request['uuid'], request['respond']
                    parameters = {key: value for key, value in request.items()
                                if key not in ['command', 'uuid', 'respond']}
                    if command == 'quit':
                        self.worker_status = 'quitting'
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
                            response = self._response(command, uuid, success, response_params)
                            with self.response_lock: self.responseQ.put(response)
                else:
                    self.worker_status = 'running'
                    
                    self.no_request_function()
                self.post_request_function()
                self._maintain_loop_time()
                

        try:
            self.cleanup_handler()
            if command == 'quit' and respond:
                response = self._response('quit', uuid, True, None)
                with self.response_lock: self.responseQ.put(response)
            self.worker_status = 'finished'
        except Exception as e:
            """
            Exception handling for cleanup errors.
            Prints the error message.
            """
            print("Error in cleanup of ThreadProcess:", id(self.worker))
            traceback.print_exc()
    
    def pre_request_function(self):
        """
        Placeholder method for monitoring events.

        This method should be overridden in subclasses to provide specific event monitoring functionality.

        Returns:
            None

        """
        return None  

    def no_request_function(self):
        """
        Placeholder method for handling no requests.

        This method should be overridden in subclasses to provide specific functionality.

        Returns:
            None

        """
        return None

    def post_request_function(self):
        """
        Placeholder method for handling post-request tasks.

        This method should be overridden in subclasses to provide specific functionality.

        Returns:
            None

        """
        return None      
    
    def request(self, command, parameters={}, respond=False):
        """
        Sends a request to the worker process/thread.

        Args:
            command (str): The command to be executed.
            parameters (dict): Additional parameters for the request.
            respond (bool): Flag indicating whether a response is expected for the request.

        Returns:
            str: The unique identifier (UUID) of the request.

        """
        request = parameters.copy()
        request.update({'command': command, 'respond': respond})
        request['uuid'] = str(uuid.uuid4())
        self.requestQ.put(request)
        return request['uuid']

    def response(self, id=None, timeout=None):
        """
        Retrieves a response from the worker process/thread.

        Args:
            id (UUID or None): The UUID of the response to retrieve.
            timeout (float or None): The maximum time to wait for a response in seconds.

        Returns:
            tuple or None:
            Returns a tuple containing the command, UUID, success flag,
            and response parameters of the retrieved response.
            If no response is available within the specified timeout, it returns None.
        """
        def retrieve_uuid_response(start_time=None):
            response = None
            q_items = []
            for _ in range(self.responseQ.qsize()):
                trial_response = self.responseQ.get()
                if trial_response.uuid == id:
                    response = trial_response
                else:
                    q_items.append(trial_response)
            for item in q_items:
                self.responseQ.put(item)
            if response is not None:
                return response
            else:
                # Effectively block by looping until the id is found
                if start_time is not None and time.time() - start_time > timeout:
                    raise TimeoutError("Timeout waiting for response.")
                else:
                    return None

        start_time = time.time()

        while True:
            try:
                if timeout is None and id is None:
                    # Get next item blocking
                    response = self.responseQ.get()
                    if response.command == 'quit': self.master_status = 'quitting'
                    return response

                elif timeout is None and id is not None:
                    # Get 'id' item blocking
                    with self.response_lock:  # Lock the queue
                        response =  retrieve_uuid_response()
                    if response is not None: 
                        if response.command == 'quit': self.master_status = 'quitting'
                        return response

                elif timeout is not None and id is None:
                    # Get next item non-blocking
                    response = self.responseQ.get(timeout=timeout)
                    if response.command == 'quit': self.master_status = 'quitting'
                    return response

                elif timeout is not None and id is not None:
                    # Get 'id' item non-blocking
                    with self.response_lock:  # Lock the queue
                        response = retrieve_uuid_response(start_time)
                    if response is not None:
                        if response.command == 'quit': self.master_status = 'quitting'
                        return response
                time.sleep(0.001)

            except queue.Empty:
                return None


    def quit(self, blocking=True):
        """
        Sends a quit request to the worker process/thread and optionally waits until the quit request is processed.

        Args:
            blocking (bool): Flag indicating whether to wait for the quit request to be processed.

        """
        id = self.request('quit', respond=True)
        while blocking and self.worker_status == 'running':            
            blocking = self.master_status != 'quitting'
            time.sleep(0.001)
        self.master_status = 'finished'
    
    import time

    def _maintain_loop_time(self):
        """
        Maintains the loop time by sleeping if necessary.

        This method calculates the time elapsed since the last loop iteration,
        and sleeps for the remaining time until the target loop period is reached.
        """
        time_now = time.time()
        current_loop_period = time_now - self.last_loop_time
        sleep_time = self.target_loop_period - current_loop_period

        # If the loop iteration took less time than the target period, sleep for the remaining time
        if sleep_time > 0:
            time.sleep(sleep_time)

        self.last_loop_time = time_now

    class _response():
        """
        A helper class representing a response object.

        Attributes:
            command (str): The command associated with the response.
            uuid (str): The unique identifier associated with the response.
            success (bool): Flag indicating the success of the response.
            result: The result or data associated with the response.

        """
        def __init__(self, command, uuid, success, result):
            """
            Initializes the _response object.

            Args:
                command (str): The command associated with the response.
                uuid (str): The unique identifier associated with the response.
                success (bool): Flag indicating the success of the response.
                result: The result or data associated with the response.

            """
            self.command = command
            self.uuid = uuid
            self.success = success
            self.result = result        

if __name__ ==  '__main__':
    print('Main process started')
    
        
