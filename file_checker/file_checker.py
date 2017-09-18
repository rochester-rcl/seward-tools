import lxml.etree as ET
from itertools import zip_longest
import collections
import os


class FileChecker(object):
    def __init__(self, directory, fix):
        self.directory = directory
        self.report = None
        self.fix = fix

    def file_checker(self, directory, extension, path):
        file_list = []
        error_dict = {}
        error_list = []
        for dirname, dirnames, filenames in os.walk(
                directory):  # Loop through the directory passed from --directory argument
            for in_file in filenames:
                file_info = collections.namedtuple('FileInfo', ['directory', 'filename', 'ext'])  # immutable
                if path is True:
                    file_path = os.path.abspath(os.path.join(dirname, in_file))
                    file_list.append(
                        file_info(directory=dirname, filename=file_path, ext=os.path.splitext(file_path)[1]))
                else:
                    file_list.append(file_info(directory=dirname, filename=in_file, ext=os.path.splitext(in_file)[1]))

        extensions_list = [info for info in file_list if info.ext == extension]

        if len(extensions_list) == 0:
            error_info = collections.namedtuple('ErrorInfo', ['directory', 'ext', 'reason'])
            error_msg = error_info(directory=dirname, ext=extension, reason='xml file missing')
            error_list.append(error_msg)
            return error_list
        else:
            return extensions_list

    def dom_checker(self, xml_file, jpg_file_list):
        xml_id = ET.QName('version="1.0" encoding="UTF-8"', 'xml')
        parser = ET.XMLParser(ns_clean=True)
        dom_tree = ET.parse(xml_file)
        root = dom_tree.getroot()
        facs = root.xpath('//tei:graphic', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        psn = root.xpath('//tei:persName', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        place = root.xpath('//tei:placeName', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        last_graphic = root.xpath('//tei:graphic[last()]', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
        error_list = []
        graphic_error_list = []
        error_return_val = {}
        xml_return_dict = {}  # mutable
        i = 1
        for graphic, jpg_file in zip_longest(facs, jpg_file_list, fillvalue=None):

            if graphic is not None and jpg_file is not None:
                if graphic.attrib['url'] != jpg_file.filename:
                    graphic.attrib['url'] = jpg_file.filename
                    error_return_val['fixedGraphicUrl'] = True
                    graphic_error_list.append(error_return_val)
                else:
                    error_return_val['fixedGraphicUrl'] = False

            if graphic is None:

                formatted_id = "i_{}_p{}".format(xml_file.split('/')[-1][2:-4], i)
                graphic_element = ET.Element("graphic", id=formatted_id, url=jpg_file.filename)
                last_graphic[-1].addnext(graphic_element)
                last_graphic.append(graphic_element)
                error_return_val['imgCountMismatch'] = True

            elif jpg_file is None:
                error_return_val['imgCountMismatch'] = True

            else:
                error_return_val['imgCountMismatch'] = False

            i += 1

            print(i)

        if len(graphic_error_list) > 0:
            error_return_val['fixedGraphicUrl'] = True

        else:
            error_return_val['fixedGraphicUrl'] = False

        print(error_return_val['fixedGraphicUrl'])

        # check for psn prefix
        missing_persons = [person.attrib['ref'] for person in psn if 'psn:' not in person.attrib['ref']]
        missing_places = [placeName.attrib['ref'] for placeName in place if 'pla:' not in placeName.attrib['ref']]
        filtered_persons = [ref for ref in missing_persons if 'spp:' not in ref]

        if len(filtered_persons) > 0 or len(missing_places) > 0:
            if filtered_persons:
                for missing in filtered_persons:
                    for pers_name in psn:
                        if pers_name.attrib['ref'] == missing:
                            pers_name.attrib['ref'] = 'psn:' + pers_name.attrib['ref']
                            error_return_val['fixedPrefix'] = True
            if missing_places:
                for missing in missing_places:
                    for place_name in place:
                        if place_name.attrib['ref'] == missing:
                            place_name.attrib['ref'] = 'pla:' + place_name.attrib['ref']
                            error_return_val['fixedPrefix'] = True

        else:
            error_return_val['fixedPrefix'] = False

        if error_return_val['fixedGraphicUrl'] is True:
            xml_return_dict['graphicError'] = 'url mismatch'

        if error_return_val['fixedPrefix'] is True:
            xml_return_dict['prefixError'] = 'missing psn or pla prefix'

        if error_return_val['imgCountMismatch'] is True:
            xml_return_dict['imgCountMismatch'] = "number of graphic tags and page breaks don't match number of images"

        xml_return_dict['tree'] = root
        xml_return_dict['output'] = xml_file
        xml_return_dict['filename'] = xml_file

        error_list.append(xml_return_dict)
        return error_list

    def xml_report(self):
        jpg_files = self.file_checker(self.directory, '.jpg', False)
        xml_file = self.file_checker(self.directory, '.xml', True)

        if 'xml file missing' in xml_file[0]:
            xml_err = {}
            print('no {} found in {}'.format(xml_file.ext, xml_file.directory))
            xml_err['reason'] = 'xml file missing'
            xml_err['directory'] = xml_file[0].directory
            xml_err['message'] = 'no {} found in {}'.format(xml_file[0].ext, xml_file[0].directory)
            return xml_err
        else:
            xml_fixed = self.dom_checker(xml_file[0].filename, jpg_files)
            if 'prefixError' in xml_fixed[0] or 'graphicError' in xml_fixed[0] or 'imgCountMismatch' in xml_fixed[0]:
                if self.fix is True:
                    dom_tree = ET.ElementTree(xml_fixed[0]['tree'])
                    dom_tree.write(xml_fixed[0]['output'], pretty_print=True)
                return xml_fixed
