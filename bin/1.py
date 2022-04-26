#!/usr/bin/env python3

import random
import typing
import uuid
import xml.dom.minidom

# Meta
__version__ = '1.0.0'
__author__ = 'https://md.land/md'
__all__ = (
    # Meta
    '__version__',
    '__author__',
    # Contract
    'CreateReportInterface',
    # Implementation
    'CreateReportWithXml',
    'CreateReportWithRaw',
    'create_example_report',
    'main',
)


# Contract
class CreateReportInterface:
    """ Creates report (file that will be stored inside an archive) """
    def with_(
        self,
        # design notice: keep function clean (without some random side effect)
        id_: str,
        level: str,
        object_name_list: typing.List[str]
    ) -> str:
        raise NotImplementedError


# Implementation
class CreateReportWithXml(CreateReportInterface):
    def __init__(self):
        import xml.dom.minidom  # lazy import in case when this concrete strategy is used
        self._minidom = xml.dom.minidom

    def with_(self, id_: str, level: str, object_name_list: typing.List[str]) -> bytes:
        xml_document_builder = self._minidom.getDOMImplementation()
        document_builder = xml_document_builder.createDocument(None, "root", None)
        assert isinstance(document_builder, xml.dom.minidom.Document)  # just for IDE hints

        top_element = document_builder.documentElement
        assert isinstance(top_element, xml.dom.minidom.Element)

        if True:  # create first `var` element
            id_element = document_builder.createElement('var')
            assert isinstance(id_element, xml.dom.minidom.Element)

            id_element.setAttribute('name', 'id')
            id_element.setAttribute('value', str(uuid.uuid4()))
            top_element.appendChild(id_element)

        if True:  # create second `var` element
            level_element = document_builder.createElement('var')
            assert isinstance(level_element, xml.dom.minidom.Element)

            level_element.setAttribute('name', 'level')
            level_element.setAttribute('value', str(random.randint(1, 100)))
            top_element.appendChild(level_element)

        if True:  # create `objects` elements
            objects_element = document_builder.createElement('objects')
            top_element.appendChild(objects_element)

            for object_name in object_name_list:
                object_element = document_builder.createElement('object')
                object_element.setAttribute('name', object_name)
                objects_element.appendChild(object_element)

        assert isinstance(top_element.parentNode, xml.dom.minidom.Document)

        return top_element.parentNode.toprettyxml(indent='  ')


class CreateReportWithRaw(CreateReportInterface):
    def with_(self, id_: str, level: str, object_name_list: typing.List[str]) -> str:
        # todo just build document as a text, not using XML DOM API
        raise NotImplementedError


def create_example_report(create_report_action: CreateReportInterface) -> str:
    id_ = str(uuid.uuid4())
    level = str(random.randint(1, 100))
    object_name_count = random.randint(1, 10)
    object_name_list = [str(uuid.uuid4()) for _ in range(1, object_name_count)]  # there is no need to complicate

    return create_report_action.with_(id_=id_, level=level, object_name_list=object_name_list)
    # todo consider to assert data structure is valid


def main(
    archive_directory_path: str,
    archive_file_count: int,
    report_file_count: int,
    create_report_action: CreateReportInterface = None,
) -> int:
    # assume `archive_directory_path` directory is exists and available, skip all access checks ...
    import zipfile  # lazy import in case function is invoked
    create_report_action = create_report_action or CreateReportWithXml()  # design notice: function still clean

    for archive_file_number in range(0, archive_file_count):
        archive = zipfile.ZipFile(f'{archive_directory_path}/{archive_file_number!s}.zip', 'w')
        with archive as archive_handle:
            for report_file_number in range(0, report_file_count):
                example_report = create_example_report(create_report_action=create_report_action)
                # probably, file extension may be changed due to used strategy,
                # todo consider to place file extension getter into strategy contract
                archive_handle.writestr(f'{report_file_number!s}.xml', data=example_report)

    return 0


if __name__ == '__main__':
    import os.path  # lazy import in case function is invoked

    # arrange
    archive_directory_path = os.path.abspath(os.path.dirname(__file__) + '/../var/xml')  # assume this directory created
    archive_file_count = 50
    report_file_count = 100  # per archive

    # act
    exit_code = main(
        archive_directory_path=archive_directory_path,
        archive_file_count=archive_file_count,
        report_file_count=report_file_count,
    )
    exit(exit_code)
