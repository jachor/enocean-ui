import logging
from .radio import start_radio
from .web import start_web
from twisted.internet import reactor


def main():
    logging.basicConfig(level='DEBUG')
    start_radio()
    start_web()
    reactor.run()


main()

