import time
import requests

import config
from config import get_config,cfg
import os

from eml_parser import serialize_mail
from connection import IMAPClient
from raven import Client
import kanboard
import kanboard_api
import mailparser
import configparser

import logging

import log




def main():


    # cfg = configparser.ConfigParser()
    # cfg.read('app.ini')

    log_level = cfg["LOG"]['log_level']
    log_filepath = cfg["LOG"]['log_path']

    logger = log.setup_custom_logger('root',log_filepath,"daemon",log_level)
    logger.info('Starting application configuration')

    #Override environement variable in debug mode
    # if cfg["APP"]['app_mode'] == "DEBUG" :
    # os.environ['IMAP_URL'] = cfg["IMAP"]['imap_url']
    # os.environ['WEBHOOK_URL'] = cfg["KANBOARD"]['api_url']
    # os.environ['KB_API_KEY'] = cfg["KANBOARD"]['api_key']
    # os.environ['KB_PJ_ID'] = cfg["KANBOARD"]["project_id"]
    # os.environ["DELAY"]=cfg["APP"]["delay"]

    # logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s > %(name)s - %(levelname)s - %(message)s',
    #                     level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')

    # config = get_config(os.environ)
    session = requests.Session()
    session_spam = requests.Session()

    # print("Configuration: ", config)



    logger.debug("Loaded configuration")
    # logger.debug("Loaded configuration: {}".format(str(config)))
    # if config['sentry_dsn']:
    #     sentry_client = Client(config['sentry_dsn'])
    #     with sentry_client.capture_exceptions():
    #         loop(config, session, sentry_client)
    # # else:
    #     loop(config, session, None)

    loop(config, session, None)


def loop(config, session,session_spam, sentry_client=None):
    logger = logging.getLogger('root')

    logger.info("Starting IMAP client Daemon loop")

    kb = kanboard_api.KanboardApi(cfg["KANBOARD"]["project_id"],cfg["KANBOARD"]["api_url"],cfg["KANBOARD"]["api_key"])
    # kb = kanboard_api.KanboardApi(config["kb"]["project_id"],config["kb"]["api_url"],config["kb"]["api_key"])

    while True:

        config

        any_message_inbox = False
        any_message_spam = False

        try :
            client = IMAPClient(config)
            connected = True
        except Exception as e:
            connected = False
            if (logger.getEffectiveLevel() < logging.INFO) :
                logger.exception("IMAP connexion error for INBOX folder")
            else :
                logger.warning("IMAP connexion error for INBOX folder")


        if connected:
            msg_ids = client.get_mail_ids()

            logger.info("Daemon found {} mails to download".format(len(msg_ids)))
            # print("Found {} mails to download".format(len(msg_ids)))
            if len(msg_ids) > 0 :
                logger.debug("Identified following msg id {}".format( msg_ids))
            # print("Identified following msg id {}", msg_ids)

            any_message_inbox = bool(msg_ids)
            if msg_ids:
                process_msg(kb,client, msg_ids[0], config, session, sentry_client)
            client.expunge()
            client.connection_close()

        try :
            ##Checking also in spam folder
            client_spam = IMAPClient(config,checkspam=True)
            spam_connected = True

        except Exception as e:
            spam_connected = False

            if (logger.getEffectiveLevel() < logging.INFO) :
                logger.exception("IMAP connexion Error for SPAM folder")
            else :
                logger.warning("IMAP connexion Error for spam folder")

        if spam_connected:
            spam_msg_ids = client_spam.get_mail_ids()

            logger.info("Daemon found {} spams to download".format(len(spam_msg_ids)))

            if len(spam_msg_ids) > 0 :
                logger.debug("Identified following msg id {}".format(spam_msg_ids))
            # print("Found {} spams to download".format(len(spam_msg_ids)))
            # print()

            any_message_spam = bool(spam_msg_ids)
            if spam_msg_ids:
                process_msg(kb,client_spam, spam_msg_ids[0], config, session_spam, sentry_client,isspam = True)

            client_spam.expunge()
            client_spam.connection_close()


        if not any_message_spam or not any_message_inbox :

            logger.info("Waiting {} seconds".format(config.app_delay))#cfg["APP"]['delay']))
            time.sleep(config.app_delay)#cfg["APP"]['delay'])

            logger.info("Resume after delay")

def process_msg(kb,client, msg_id, config, session, sentry_client=None,isspam = False):
    logger = logging.getLogger('root')

    logger.debug("Fetch message ID {}".format(msg_id))
    start = time.time()
    raw_mail = client.fetch(msg_id)
    end = time.time()
    logger.debug("Message downloaded in {} seconds".format(end - start))

    try:
        start = time.time()

        mail = mailparser.parse_from_bytes(raw_mail)

        logger.debug("Creating task into kanboard ")

        # kb = kanboard.Client(config["kb"]["api_url"], 'jsonrpc', config["kb"]["api_key"])

        task_id = kb.create_task_from_eml(mail,isspam=isspam)

        logger.debug("Created task with id {} :".format(task_id))

        if task_id is not None :
            if cfg['IMAP']['on_success'] == 'delete':
                client.mark_delete(msg_id)
                logger.debug("Deleting message with id {}".format(msg_id))
            elif cfg['IMAP']['on_success'] == 'move':
                client.move(msg_id, cfg['IMAP']['success'])
                logger.debug("Moving message with id {}".format(msg_id))
            else:
                logger.debug("Nothing to do for message id {}".format(msg_id))

    except Exception as e:
        if sentry_client:
            sentry_client.captureException()
        client.move(msg_id, config['imap']['error'])
        logger.exception("Unable to parse or delivery msg")


if __name__ == '__main__':
    main()
