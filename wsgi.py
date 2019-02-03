#!/usr/bin/python

#
# gunicorn WSGI Entry Point
#
# To run this application as www-data on Raspberry Pi
# create systemd service.
# See https://github.com/lhost/rpi-scripts/blob/master/nodemcu-webdriver.sh for example

from webdriver import app

application = app

if __name__ == "__main__":
    application.run()
