from urllib.parse import parse_qs, urlparse, unquote

import configparser
import imaplib

cfg = configparser.ConfigParser()
cfg.read('./config/app.ini')


app_delay = int(cfg["APP"]["delay"])


# debug_level = cfg["LOG"]['log_level']
# debug_filepath = cfg["LOG"]['log_path']

transports = {
    'imap': [imaplib.IMAP4, 143],
    'imap+ssl': [imaplib.IMAP4_SSL, 993]
}




def default_qs(qs, key, default):
    return parse_qs(qs)[key][0] if key in parse_qs(qs) else default


def get_config(env):
    imap_parse = urlparse(env['IMAP_URL'])
    webhook = env['WEBHOOK_URL']
    username = unquote(imap_parse.username) if imap_parse.username else None
    password = unquote(imap_parse.password) if imap_parse.password else None
    api_key = env['KB_API_KEY']
    project_id = env['KB_PJ_ID']
    return {
        'imap': {
            'hostname': imap_parse.hostname,
            'username': username,
            'password': password,
            'protocol': imap_parse.scheme,
            'transport': transports[imap_parse.scheme][0],
            'port': transports[imap_parse.scheme][1],
            'inbox': default_qs(imap_parse.query, 'inbox', 'INBOX'),
            'spam': default_qs(imap_parse.query, 'spam', 'SPAM'),
            'error': default_qs(imap_parse.query, 'error', 'ERROR'),
            'on_success': env.get('ON_SUCCESSS', 'move'),
            'success': default_qs(imap_parse.query, 'success', 'SUCCESS'),
        },
        'webhook': webhook,
        "kb" : {
            "api_key" : api_key,
            "api_url" : webhook,
            "project_id" : project_id
            },
        'compress_eml': env.get('COMPRESS_EML', 'false') == 'true',
        'delay': int(env['DELAY']) if 'DELAY' in env else 60,
        'sentry_dsn': env.get('SENTRY_DSN', None)
    }
