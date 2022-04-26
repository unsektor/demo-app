#!/usr/bin/env python3
import csv
import queue
import typing

import lxml
import lxml.cssselect
import lxml.html
import lxml.etree

import threading

# Meta
__version__ = '1.0.0'
__author__ = 'https://md.land/md'
__all__ = (
    # Meta
    '__version__',
    '__author__',
    # Implementation
    'CreateFirstReportModelXml',
    'CreateSecondReportModelXml',
    'main',
)

# Implementation
class CreateFirstReportModelXml:  # there is no need to extract common contract to build reports' models (overkill for this example)
    def __init__(self):
        self._var_id_element_selector = lxml.cssselect.CSSSelector("root > var[name=id]")
        self._var_level_element_selector = lxml.cssselect.CSSSelector("root > var[name=level]")

    def from_content(self, root: lxml.etree.XML) -> typing.List[dict]:
        # Retrieve `root > var[name=id]` `value` attribute value
        var_id_element_list = list(self._var_id_element_selector(root))
        assert len(var_id_element_list) == 1
        var_id_element = var_id_element_list[0]
        assert isinstance(var_id_element, lxml.etree._Element)
        id_value = var_id_element.get('value')

        # Retrieve `root > var[name=id]` `value` attribute value
        var_level_element_list = list(self._var_level_element_selector(root))
        assert len(var_level_element_list) == 1
        var_level_element = var_level_element_list[0]
        assert isinstance(var_level_element, lxml.etree._Element)
        level_value = var_level_element.get('value')

        return [{'id': id_value, 'level': level_value}]


class CreateSecondReportModelXml:
    def __init__(self):
        self._var_id_element_selector = lxml.cssselect.CSSSelector("root > var[name=id]")
        self._object_name_element_selector = lxml.cssselect.CSSSelector("root > objects > object")

    def from_content(self, root: lxml.etree.XML) -> typing.Iterable[dict]:
        # Retrieve `root > var[name=id]` `value` attribute value
        # design notice: here is some WET code: it's okay to keep report create actions independent to each other
        var_id_element_list = list(self._var_id_element_selector(root))
        assert len(var_id_element_list) == 1
        var_id_element = var_id_element_list[0]
        assert isinstance(var_id_element, lxml.etree._Element)
        id_value = var_id_element.get('value')

        # Retrieve `root > var[name=id]` `value` attribute value
        object_name_element_list = list(self._object_name_element_selector(root))
        for object_name_element in object_name_element_list:
            assert isinstance(object_name_element, lxml.etree._Element)
            object_name = object_name_element.get('name')
            yield {'id': id_value, 'object_name': object_name}


def main(
    archive_directory_path: str,
    report_directory_path: str,
    threads_count: int,
) -> int:
    # assume `archive_directory_path` directory is exists and available, skip all access checks and etc ...
    import zipfile  # lazy import in case function is invoked

    # Init dependencies
    create_first_report_model_xml = CreateFirstReportModelXml()
    create_second_report_model_xml = CreateSecondReportModelXml()

    report_1_file = open(report_directory_path + '/1.csv', 'w', newline='')
    report_1 = csv.DictWriter(report_1_file, fieldnames=['id', 'level'], dialect='excel')

    report_2_file = open(report_directory_path + '/2.csv', 'w', newline='')
    report_2 = csv.DictWriter(report_2_file, fieldnames=['id', 'object_name'], dialect='excel')

    arhive_file_processing_queue = queue.Queue()

    # act
    report_1.writeheader()
    report_2.writeheader()

    for archive_file in os.listdir(archive_directory_path):
        if not archive_file.lower().endswith('.zip'):
            continue

        archive_path = f'{archive_directory_path}/{archive_file!s}'
        archive = zipfile.ZipFile(archive_path, 'r')

        with archive:
            for file in archive.filelist:
                # assume there is only xml files according to task requirements
                if not file.orig_filename.lower().endswith('.xml'):
                    continue

                arhive_file_processing_queue.put((archive_path, file))

    def process_archive_file() -> None:  # probably could be extracted to independent, but no necessity atm
        while True:
            archive_path, file = arhive_file_processing_queue.get()
            archive = zipfile.ZipFile(archive_path, 'r')

            with archive as archive_handle:
                content = archive_handle.read(file)
                root = lxml.etree.XML(content)  # reuse this instance across reports builders

                model1_iterable = create_first_report_model_xml.from_content(root=root)
                report_1.writerows(model1_iterable)

                # design notice: there it is not good to create few reports at once,
                #                better to separate responsibilities.
                #                but for simpler implementation, here is resource handle reuse way

                model2_iterable = create_second_report_model_xml.from_content(root=root)
                report_2.writerows(model2_iterable)

                report_1_file.flush()
                report_2_file.flush()

                arhive_file_processing_queue.task_done()

    for i in range(threads_count):
        thread = threading.Thread(target=process_archive_file, daemon=True)
        thread.start()

    arhive_file_processing_queue.join()

    report_1_file.flush()
    report_1_file.close()

    report_2_file.flush()
    report_2_file.close()
    return 0


if __name__ == '__main__':
    import os  # lazy import in case function is invoked

    # arrange
    # ... assume these directories created (and contains only valid files) and has no access issues, skip related checks
    var_directory_path = os.path.abspath(os.path.dirname(__file__) + '/../var')
    archive_directory_path = f'{var_directory_path!s}/xml'
    report_directory_path = f'{var_directory_path!s}/csv'
    threads_count = os.cpu_count() * 2  # for this task there is no need for special management or `multiprocessing` use

    # act
    exit_code = main(
        archive_directory_path=archive_directory_path,
        report_directory_path=report_directory_path,
        threads_count=threads_count,
    )
    exit(exit_code)
