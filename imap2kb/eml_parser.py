import base64
import binascii
import gzip
import json
import quopri
import re
import uuid
import os
from io import BytesIO

import mailparser
import talon
from html2text import html2text


talon.init()

decoder_map = {
    'base64': base64.b64decode,
    '': lambda payload: payload.encode('utf-8'),
    '7bit': lambda payload: payload.encode('utf-8'),
    'quoted-printable': quopri.decodestring
}

JSON_MIME = 'application/json'
GZ_MIME = 'application/gzip'
EML_MIME = 'message/rfc822'
BINARY_MIME = 'application/octet-stream'


def get_text(mail):
    raw_content, html_content, plain_content, html_quote, plain_quote = '', '', '', '', ''

    if mail.text_html:
        raw_content = ''.join(mail.text_html).replace('\r\n', '\n')
        html_content = talon.quotations.extract_from_html(raw_content)
        html_quote = raw_content.replace(html_content, '')
        plain_content = html2text(html_content)

    if mail.text_plain or not plain_content:
        raw_content = ''.join(mail.text_plain)
        plain_content = talon.quotations.extract_from_plain(raw_content)
        plain_quote = raw_content.replace(plain_content, '')

    # 'content' item holds plain_content and 'quote' item holds plain_quote (with HTML stripped off).
    # These names are used for backward compatibility.
    return {
        'html_content': html_content,
        'content': plain_content,
        'html_quote': html_quote,
        'quote': plain_quote
    }


def get_auto_reply_type(mail):
    if 'report-type=disposition-notification' in mail.content_type:
        return 'disposition-notification'
    if mail.auto_submitted and mail.auto_submitted.lower() == 'auto-replied':
        return 'vacation-reply'
    return None


def get_to_plus(mail):
    to_plus = set([x[1] for x in mail.to] if mail.to else [])

    if mail.delivered_to:
        to_plus.update(x[1] for x in mail.delivered_to)
    if mail.cc:
        to_plus.update(x[1] for x in mail.cc)
    if mail.bcc:
        to_plus.update(x[1] for x in mail.bcc)
    to_plus.update(
        match.group(1)
        for match in
        [
            re.search(r'for ([a-zA-Z0-9\-]+@[a-zA-Z.]+)', r['others'])
            for r in mail.received
            if 'others' in r
        ]
        if match
    )
    to_plus.update(r['for'] for r in mail.received if 'for' in r)
    return list(to_plus)


def get_attachments(mail):
    attachments = []
    for attachment in mail.attachments:
        if attachment['content_transfer_encoding'] not in decoder_map:
            msg = "Invalid Content-Transfer Encoding ({}) in msg {}.".format(
                attachment['content_transfer_encoding'], mail.message_id
            )
            raise Exception(msg)
        decoder = decoder_map[attachment['content_transfer_encoding']]

        filename = attachment['filename']

        try:
            content = decoder(attachment['payload'])
            attachments.append((
                filename,
                BytesIO(content),
                BINARY_MIME
            ))
        except (binascii.Error, ValueError):
            print("Unable to parse attachment '{}' in {} \n".format(filename, mail.message_id))
    return attachments


def get_eml(raw_mail, compress_eml):
    content = raw_mail

    if compress_eml:
        file = BytesIO()
        with gzip.open(file, 'wb') as f:
            f.write(raw_mail)
        content = file.getvalue()
    return content

def extract (msgfilecontent, key):
    """Extracts all data from e-mail, including From, To, etc., and returns it as a dictionary.
    msgfile -- A file-like readable object
    key     -- Some ID string for that particular Message. Can be a file name or anything.
    Returns dict()
    Keys: from, to, subject, date, text, html, parts[, files]
    Key files will be present only when message contained binary files.
    For more see __doc__ for pullout() and caption() functions.
    """
    m = message_from_file(msgfile)
    From, To, Subject, Date = caption(m)
    Text, Html, Files, Parts = pullout(m, key)
    Text = Text.strip(); Html = Html.strip()
    msg = {"subject": Subject, "from": From, "to": To, "date": Date,
        "text": Text, "html": Html, "parts": Parts}
    if Files: msg["files"] = Files
    return msg


def open_eml(filepath,mailfile) : 

    #f = open(os.path.join(os.path.normpath(filepath),mailfile), "r")
    mail  =  mailparser.parse_from_file(os.path.join(os.path.normpath(filepath),mailfile))
    #f.close()
    
    print(mail)
    return mail
        


def serialize_mail(raw_mail, compress_eml=False):
    mail = mailparser.parse_from_bytes(raw_mail)
    files = []
    # Build manifest
    body = {
        'headers': {
            'subject': mail.subject,
            'to': [x[1] for x in mail.to] if mail.to else [],
            'to+': get_to_plus(mail),
            'from': [x[1] for x in mail._from] if mail.from_ else [],
            'date': mail.date.isoformat() if mail.date else [],
            'cc': [x[1] for x in mail.cc] if mail.cc else [],
            'message_id': mail.message_id,
            'auto_reply_type': get_auto_reply_type(mail)
        },
        'version': 'v2',
        'text': get_text(mail),
        'files_count': len(mail.attachments),
        'eml': {
            'compressed': compress_eml,
        }
    }
    files.append(
        ('manifest', ('manifest.json', BytesIO(json.dumps(body).encode('utf-8')), JSON_MIME))
    )
    # Build eml
    eml_ext = 'eml.gz' if compress_eml else 'eml'
    eml_name = "{}.{}".format(uuid.uuid4().hex, eml_ext)
    eml_mime = GZ_MIME if compress_eml else EML_MIME

    files.append(
        ('eml', (eml_name, BytesIO(get_eml(raw_mail, compress_eml)), eml_mime))
    )
    # Build attachments
    for att in get_attachments(mail):
        files.append(('attachment', att))
    return files
