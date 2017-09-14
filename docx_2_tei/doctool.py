import os
import zipfile
import http.server
import socketserver
from threading import Thread, Event

class FileError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)


class ZipError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        http.server.SimpleHTTPRequestHandler.end_headers(self)


class DocTool(object):
    def __init__(self, in_dir, out_dir):
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.files = DocTool.scan_input(in_dir)
        self.temp_dir = DocTool.create_temp_dir(in_dir)
        self.xml_files = []
        self.httpd = None
        self.server_thread = None
        self.server_running = False

    def unzip_files(self):
        prepared_files = []
        for doc_file in self.files:
            with zipfile.ZipFile(doc_file, "r") as zf:
                basename = os.path.splitext(os.path.basename(doc_file))[0]
                temp_dst = "{}/{}".format(self.temp_dir, basename)
                zf.extractall(temp_dst)
                prepared_files.append("/{}/word/document.xml".format(basename))
        if len(prepared_files) > 0:
            return prepared_files
        else:
            raise ZipError("Files were not successfully unzipped")

    def unzip_resources(self, resource_path):
        with zipfile.ZipFile(resource_path, "r") as zf:
            zf.extractall(self.temp_dir)

    def serve_files(self, port):
        os.chdir(self.temp_dir)
        cors_request_handler = CORSRequestHandler
        self.httpd = socketserver.TCPServer(("", port), cors_request_handler)
        self.httpd.allow_reuse_address = True
        self.server_thread = Thread(target=self.start_server)
        self.server_thread.stop_event = Event()
        self.server_thread.daemon = True
        self.server_thread.start()
        self.server_running = True

    def start_server(self):
        self.httpd.serve_forever()

    def kill_server(self):
        self.httpd.server_close()
        self.server_thread.stop_event.is_set()

    @staticmethod
    def create_temp_dir(directory):
        temp_dir_name = "{}/temp/".format(directory)
        if not os.path.exists(temp_dir_name):
            os.makedirs(temp_dir_name)
        print("Temp directory already exists. Using {}".format(temp_dir_name))
        return temp_dir_name

    @staticmethod
    def clean_temp_dir(temp_dir):
        for dirname, dirnames, filenames in os.walk(temp_dir):
            for filename in filenames:
                file_path = os.path.abspath(os.path.join(dirname, filename))
                if '.docx' not in file_path:
                    os.remove(file_path)

    @staticmethod
    def scan_input(directory):
        valid_files = []
        for dirname, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                if '.docx' in filename:
                    valid_files.append(os.path.abspath(os.path.join(dirname, filename)))
        if len(valid_files) > 0:
            return valid_files
        else:
            raise FileError("No docx files found!")
