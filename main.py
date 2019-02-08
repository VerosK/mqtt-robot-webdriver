#!/usr/bin/python

import webdriver
import configparser

CONFIG_FNAME = 'driver.ini'

config = configparser.ConfigParser()
config.read([CONFIG_FNAME])

#webdriver.app.debug = True
webdriver.app.run(
        host = config['webdriver']['listen'],
        port = config['webdriver']['port']
        )
