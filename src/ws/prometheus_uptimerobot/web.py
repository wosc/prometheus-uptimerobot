import prometheus_client
import prometheus_client.core
import argparse
import logging
import os
import os.path
import sys
import wsgiref.handlers
import wsgiref.simple_server

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

APP = prometheus_client.make_wsgi_app()
log = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'


class UptimeRobotCollector(object):

    def configure(self, config_file):
        config = ConfigParser()
        config.read(os.path.expanduser(config_file))
        get = lambda x: config.get('default', x)  # noqa
        self.api_key = get('api_key')

    def collect(self):
        try:
            pass
        except Exception:
            log.error('Error during collect', exc_info=True)

    def describe(self):
        pass


COLLECTOR = UptimeRobotCollector()
prometheus_client.core.REGISTRY.register(COLLECTOR)


def cgi():
    logfile = os.environ.get('PROMETHEUS_UPTIMEROBOT_LOGFILE')
    if logfile:
        logging.basicConfig(filename=logfile, format=LOG_FORMAT)
    COLLECTOR.configure(os.environ['PROMETHEUS_UPTIMEROBOT_CONFIG'])
    wsgiref.handlers.CGIHandler().run(APP)


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost', help='bind host')
    parser.add_argument('--port', default='9429', help='bind port', type=int)
    parser.add_argument('--config', help='path to config file')
    options = parser.parse_args()
    logging.basicConfig(stream=sys.stdout, format=LOG_FORMAT)
    if options.config:  # collector will raise if missing
        COLLECTOR.configure(options.config)
    wsgiref.simple_server.make_server(
        options.host, options.port, APP).serve_forever()
