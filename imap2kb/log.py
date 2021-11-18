# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 22:16:14 2021

@author: admin-tf
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from concurrent_log_handler import ConcurrentRotatingFileHandler


loglevel = {
    "DEBUG" : logging.DEBUG,
    "INFO" : logging.INFO,
    "WARNING " : logging.WARNING,
    "ERROR" : logging.ERROR,
    "CRITICAL" : logging.CRITICAL
    }

def setup_custom_logger(name,logPath,fileName,level="INFO"):
    logFormatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    # level=logging.DEBUG


    logger = logging.getLogger('root')
    logger.setLevel(loglevel.get(level,"INFO"))

    #Remove old preexisting handlers to avoid multiple prints
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    #Handle log message into the console
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    #Handle log message into the log files with rotation


    logfile = os.path.join(logPath, "{}.log".format(fileName))

    if not os.path.exists(logPath):
        os.makedirs(logPath)

    rotateHandler = ConcurrentRotatingFileHandler(logfile, "a", 512*1024, 5)
    logger.info("Initiating logging into {}".format(logfile))
    # rotateHandler = ConcurrentRotatingFileHandler("{0}/{1}.log".format(logPath, fileName), "a", 512*1024, 5)
    rotateHandler.setFormatter(logFormatter)
    logger.addHandler(rotateHandler)

    return logger