
from io import BytesIO
import docx
import xml.etree.ElementTree as ET
import xml.sax
import io

BODY = ("http://www.gribuser.ru/xml/fictionbook/2.0", "body")

class FB2Handler(xml.sax.ContentHandler):
    def __init__(self):
        self.in_body = False
        self.text = ''
    def startElementNS(self, name, qname, attrs):
        if name == BODY:
            self.in_body = True
    def endElementNS(self, name, qname):
        if name == BODY:
            self.in_body = False
    def characters(self, content):
        if self.in_body:
            self.text += content

# Надо дописать что бы забирал только автора и заголовок в начале и игнорировал примечания

class FB2Reader:
    def __init__(self, file_content):
        self.file_content = file_content

    def get_text(self):
        handler = FB2Handler()
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.setFeature(xml.sax.handler.feature_namespaces, True)
        parser.parse(io.StringIO(self.file_content))
        return handler.text
    

def get_text_from_docx_file(file):
    file_content = file.read()
    doc = docx.Document(BytesIO(file_content))
    text = '\n\n'.join([para.text for para in doc.paragraphs])
    return text


