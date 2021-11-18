import logging
import imaplib
from config import cfg


transports = {
    'imap': imaplib.IMAP4,
    'imap+ssl': imaplib.IMAP4_SSL
}

class IMAPClient(object):

    def __init__(self, config,checkspam=False):

        self.logger = logging.getLogger('root')
        transport = transports[cfg['IMAP']['transport']]
        hostname = cfg['IMAP']['hostname']
        port = cfg['IMAP']['port']


        self.client = transport(host=hostname, port=port)

        self.logger.debug("Connected to mail server")
        # print("Connected to mail server")
        username = cfg['IMAP']['username']
        password = cfg['IMAP']['password']
        if username and password:
            login = self.client.login(username, password)
            if login[0] != 'OK':
                raise Exception("Unable to login", login)

        self.logger.debug("Logged in to {}".format(hostname))
        # print("Logged in")

        if checkspam :
            "Also checking spams"
            select_folder = self.client.select(cfg['IMAP']['spam'])
        else :
            select_folder = self.client.select(cfg['IMAP']['inbox'])

        if select_folder[0] != 'OK':
            raise Exception("Unable to select folder", select_folder)

    def get_mail_ids(self):
        result_search, data = self.client.uid('SEARCH', 'ALL')
        if result_search != 'OK':
            raise Exception("Search failed!")
        return data[0].decode('utf-8').split()

    def fetch(self, msg_id):
        result_fetch, data = self.client.uid('FETCH',
                                             "{0}:{0} RFC822".format(msg_id))
        if result_fetch != 'OK':
            raise Exception("Fetch failed!")
        return data[0][1]

    def connection_close(self):
        self.client.close()
        self.logger.debug("Connection closed")
        # print("Connection closed")
        self.client.logout()

        self.logger.debug("Logged out")
        # print("Logged out")

    def move(self, msg_id, folder):
        # print("Going to move {} to {}".format(msg_id, folder))
        self.logger.debug("Going to move {} to {}".format(msg_id, folder))
        self.copy(folder, msg_id)
        self.mark_delete(msg_id)

    def mark_delete(self, msg_id):
        self.logger.debug("Going to mark as deleted {}".format(msg_id))
        # print("Going to mark as deleted {}".format(msg_id))
        delete_result, _ = self.client.uid('STORE', msg_id,
                                           '+FLAGS', '(\Deleted)')
        if delete_result != 'OK':
            raise Exception("Failed to mark as deleted msg {}".format(msg_id))

    def copy(self, folder, msg_id):
        self.logger.debug("Going to copy {} to {}".format(msg_id, folder))
        # print("Going to copy {} to {}".format(msg_id, folder))
        copy_result, data = self.client.uid('COPY', msg_id, folder)
        if copy_result != 'OK':
            self.logger.debug(copy_result)
            self.logger.debug(data)
            # print(copy_result, data)
            raise Exception("Failed to copy msg {} to {}".
                            format(msg_id, folder))

    def expunge(self):
        self.client.expunge()
