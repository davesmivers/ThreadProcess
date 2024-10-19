import unittest
from threadprocess import ThreadProcess
import os

class FileWorker(ThreadProcess):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def startup_handler(self, **startup_args):
        filename, mode = startup_args['filename'], startup_args['mode']
        self.file = open(filename, mode)

    def request_handler(self, command, uuid, parameters={}):
        if command == 'write_line':
            message = parameters['message'] + '\n'
            self.file.write(message)
            return f'Line written successfully {message}'
        elif command == 'write_line_backwards':
            message_backwards = parameters['message'][::-1] + '\n'
            self.file.write(message_backwards)
            return f'Line written backwards successfully {message_backwards}'
        elif command == 'readlines':
            return self.file.readlines()

    def cleanup_handler(self):
        self.file.close()


class TestFileWorker(unittest.TestCase):
    def setUp(self):
        self.test_filename = 'test_output.txt'
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_write_and_read(self):
        # Create an instance of FileWorker for writing
        file_worker = FileWorker(filename=self.test_filename, mode='a', runtype='thread')

        # Write a line to the file
        file_worker.request('write_line', {'message': 'knock knock'}, respond=True)
        response = file_worker.response()
        self.assertIn('Line written successfully', response.result)

        # Write a line backwards to the file
        file_worker.request('write_line_backwards', {'message': "who's there"}, respond=True)
        response = file_worker.response()
        self.assertIn('Line written backwards successfully', response.result)

        # Quit the file worker
        file_worker.quit(blocking=True)

        # Create an instance of FileWorker for reading
        file_reader = FileWorker(filename=self.test_filename, mode='r', runtype='process')

        # Read lines from the file
        file_reader.request('readlines', respond=True)
        lines = file_reader.response().result
        self.assertEqual(lines[0].strip(), 'knock knock')
        self.assertEqual(lines[1].strip(), "ereht s'ohw")

        # Quit the file reader
        file_reader.quit(blocking=True)


if __name__ == '__main__':
    unittest.main()
