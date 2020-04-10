#!/usr/bin/env python

# TODO rename all UI objects to PEP8 standard in QTCreator
import os
import sys
import csv
import json
from file_checker.file_checker import FileChecker
from docx_2_tei.doctool import DocTool, FileError, ZipError

# Qt Dependencies
from PyQt5 import QtGui
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl, QFile, QFileInfo, QIODevice
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QFileDialog, QListWidgetItem, QTabWidget
from mainwindow import Ui_MainWindow
import resources


class ScriptLoader(object):
    def __init__(self):
        # Saxon
        # ---------------------------------------------------------------------------------------------
        saxon_api = QFile(':/SaxonJS.js')
        saxon_api.open(QIODevice.ReadOnly)
        saxon_script = str(saxon_api.readAll(), encoding='utf-8')
        saxon_api.close()
        self.saxon_script = saxon_script
        # QWebChannel
        # ----------------------------------------------------------------------------------------------
        qchannel_api = QFile(":/qtwebchannel/qwebchannel.js")
        qchannel_api.open(QIODevice.ReadOnly)
        qchannel_script = str(qchannel_api.readAll(), encoding='utf-8')
        qchannel_api.close()
        self.q_channel_script = qchannel_script
        # Transform functions
        # ----------------------------------------------------------------------------------------------
        transform_js = QFile(":/transform.js")
        transform_js.open(QIODevice.ReadOnly)
        transform_script = str(transform_js.readAll(), encoding='utf-8')
        transform_js.close()
        self.transform_script = transform_script


class Handler(QObject):
    send_transform = pyqtSignal('PyQt_PyObject')
    do_cleanup = pyqtSignal('PyQt_PyObject')
    dispatch_message = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    MSG_SUCCESS = "success"
    MSG_ERROR = "error"
    MSG_INFO = "info"

    @pyqtSlot(str)
    def transform_ready(self, xml_string):
        self.send_transform.emit(xml_string)

    @pyqtSlot(str)
    def transformations_complete(self, status):
        self.dispatch_message.emit("All transformations completed!", self.MSG_SUCCESS)
        self.do_cleanup.emit(status)

    @pyqtSlot(str, str)
    def send_message(self, message, msg_type):
        self.dispatch_message.emit(message, msg_type)


class SewardQcApp(QMainWindow, Ui_MainWindow, QWidget):
    PORT = 8081
    URL_PREFIX = "http://localhost:{}".format(PORT)

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        QWidget.__init__(self)
        self.setupUi(self)

        # QC Tab
        # --------------------------------------------------------------------
        self.dir = None
        self.dir_open.clicked.connect(self.file_dialog)
        self.csv_tuples = []
        self.run_report.setEnabled(False)
        self.export_2.setEnabled(False)
        self.run_report.clicked.connect(self.file_report)
        self.export_2.clicked.connect(self.export_csv)

        # Transform Tab
        # ---------------------------------------------------------------------
        self.open_word_dir.clicked.connect(self.get_word_dir)
        self.open_output_dir.clicked.connect(self.get_out_dir)
        self.run_transformation.clicked.connect(self.transform)
        self.run_transformation.setEnabled(False)
        self.textEdit.readOnly = True
        self.webview = QWebEngineView()
        self.webview.settings().localContentCanAccessRemoteUrls = True
        self.channel = QWebChannel()
        self.handler = Handler()
        self.handler.send_transform.connect(self.save_xml)
        self.handler.dispatch_message.connect(self.add_text_to_console)
        self.handler.do_cleanup.connect(self.destroy_doc_tool)
        self.script_loader = ScriptLoader()
        self.q_channel_ready = False
        self.handler_ready = False
        self.saxon_ready = False
        self.init_q_channel()
        self.init_saxon()
        self.word_dir = None
        self.out_dir = None
        self.doc_tool = None
        self.stylesheets = ["docxtotei.sef", "sewardheader.sef", "pagebreaks.sef"]

    # Initialization
    # ---------------------------------------------------------------------------------------------
    def init_q_channel(self):
        self.channel.registerObject('handler', self.handler)
        self.webview.page().runJavaScript(self.script_loader.q_channel_script, self.set_channel)

    def init_saxon(self):
        self.webview.page().runJavaScript(self.script_loader.saxon_script, self.verify_saxon)

    def init_transform(self):
        self.webview.page().runJavaScript(self.script_loader.transform_script, self.verify_handler)

    def set_handler_status(self, status):
        self.handler_ready = status

    def set_saxon_status(self, status):
        self.saxon_ready = status

    def set_channel(self, data):
        self.webview.page().setWebChannel(self.channel)
        self.init_transform()

    def verify_handler(self, data):
        self.webview.page().runJavaScript("checkChannelInit()", self.set_handler_status)

    def verify_saxon(self, data):
        self.webview.page().runJavaScript("checkSaxonInit()", self.set_saxon_status)

    # UI Methods
    # ----------------------------------------------------------------------------------------------
    def file_dialog(self):
        self.list_widget.clear()
        dialog = QFileDialog()
        folder = dialog.getExistingDirectory(self, 'Select Directory with Letter Subfolders')

        if folder:
            self.run_report.setEnabled(True)
            self.dir = folder
            self.directory.setText(self.dir)

    def file_report(self):
        self.list_widget.clear()
        self.csv_tuples[:] = []
        if self.check_box.isChecked():
            self.fix = True
        else:
            self.fix = False

        error_list = []
        for dirname, dirnames, filenames in os.walk(self.dir):
            error_list.append(dirname)
        error_list.pop(0)

        for directory_path in error_list:
            check_folder = FileChecker(directory_path, self.fix)
            test = check_folder.xml_report()

            if isinstance(test, dict):
                if 'xml file missing' in test.values():
                    self.csv_tuples.append((test['directory'].split('/')[-1], test['message']))

            if isinstance(test, list):
                if 'url mismatch' in test[0].values():
                    for error in test:
                        self.csv_tuples.append((error['filename'].split('/')[-1], error['graphicError']))

                if 'missing psn or pla prefix' in test[0].values():
                    for error in test:
                        self.csv_tuples.append((error['filename'].split('/')[-1], error['prefixError']))

                if "number of graphic tags and page breaks don't match number of images" in test[0].values():
                    for error in test:
                        self.csv_tuples.append((error['filename'].split('/')[-1], error['imgCountMismatch']))

        if len(self.csv_tuples) > 0:
            for row in self.csv_tuples:
                row_string = ' | '.join(row)
                self.list_widget.addItem(row_string)
                self.export_2.setEnabled(True)

            if self.fix is True:
                fixed_dialog = QListWidgetItem("Corrected fixable errors")
                fixed_dialog.setForeground(QtGui.QColor("green"))
                self.list_widget.addItem(fixed_dialog)
        else:
            self.list_widget.addItem('All files check out!')

    def export_csv(self):
        dialog = QFileDialog()
        out_csv = dialog.getSaveFileName()
        if len(self.csv_tuples) > 0:
            with open(out_csv[0], 'w') as out_file:
                writer = csv.writer(out_file)
                writer.writerow(('file/folder', 'reason'))
                for row in self.csv_tuples:
                    writer.writerow(row)

        else:
            print('All files check out!')

    def get_word_dir(self):
        dialog = QFileDialog()
        folder = dialog.getExistingDirectory(self, 'Select Directory with Docx Files to Transform')

        if folder:
            if self.out_dir:
                self.run_transformation.setEnabled(True)
            self.word_dir = folder
            self.add_text_to_console("Word directory is set to {}".format(folder), self.handler.MSG_INFO)

    def get_out_dir(self):
        dialog = QFileDialog()
        folder = dialog.getExistingDirectory(self, 'Select Output Directory')

        if folder:
            if self.word_dir:
                self.run_transformation.setEnabled(True)
            self.out_dir = folder
            self.add_text_to_console("Output directory is set to {}".format(folder), self.handler.MSG_INFO)

    def add_text_to_console(self, text, msg_type):
        handler = self.handler
        if msg_type is handler.MSG_ERROR:
            self.textEdit.setTextColor(QtGui.QColor(255, 0, 0))
        if msg_type is handler.MSG_SUCCESS:
            self.textEdit.setTextColor(QtGui.QColor(0, 100, 0))
        self.textEdit.insertPlainText("{}\n\n".format(text))
        self.textEdit.verticalScrollBar().setValue(self.textEdit.verticalScrollBar().maximum())
        self.textEdit.setTextColor(QtGui.QColor(0, 0, 0))

    def closeEvent(self, event):
        if self.doc_tool and self.doc_tool.server_running:
            self.doc_tool.kill_server()
            event.accept()

    def save_xml(self, xml_string):
        doc_info = json.loads(xml_string)
        new_name = "{}{}".format(self.prepend_text_edit.toPlainText(), doc_info["name"])
        saved = self.doc_tool.save_xml(new_name, doc_info["xml"], doc_info["name"])

        if saved:
            self.add_text_to_console("{} saved to {}".format(new_name, self.out_dir), self.handler.MSG_SUCCESS)
        else:
            self.add_text_to_console("Unabled to save {} to {}".format(new_name, self.out_dir), self.handler.MSG_ERROR)

    # Transformation stuff
    def transform(self):
        self.doc_tool = DocTool(self.word_dir, self.out_dir)
        try:
            unzipped_files = self.doc_tool.unzip_files()
            doc_name = lambda file_path: file_path.split('/')[-3]
            prepared_files = [{"name": doc_name(xml_path), "file": "{}{}".format(self.URL_PREFIX, xml_path)} for
                              xml_path in unzipped_files]
            if not self.doc_tool.server_running:
                self.doc_tool.serve_files(self.PORT)
            resources_zip = SewardQcApp.copy_resources(':/from.zip', self.doc_tool.temp_dir)
            self.doc_tool.unzip_resources(resources_zip)
            stylesheets = json.dumps(
                ["{}/from/{}".format(self.URL_PREFIX, stylesheet) for stylesheet in self.stylesheets])
            serialized = json.dumps(prepared_files)
            self.webview.page().runJavaScript("prepareSources({},{});".format(stylesheets, serialized))
        except ZipError as error:
            self.add_text_to_console(error, self.handler.MSG_ERROR)

    def destroy_doc_tool(self):
        self.doc_tool.kill_server()
        self.doc_tool.clean_temp_dir()
        self.doc_tool = None

    @staticmethod
    def copy_resources(src, dst):
        resource_zip = QFile(src)
        resource_zip.open(QIODevice.ReadOnly)
        data = bytearray(resource_zip.readAll())
        resource_zip.close()
        dst_file = "{}{}".format(dst, QFileInfo(src).fileName())
        try:
            with open(dst_file, 'wb') as zipped_resources:
                zipped_resources.write(data)
            return dst_file
        except IOError as error:
            print(error)
            return False


if __name__ == "__main__":
    # Set up GUI
    app = QApplication(sys.argv)
    window = SewardQcApp()
    window.setWindowTitle('Seward QC App')
    window.show()
    sys.exit(app.exec_())
