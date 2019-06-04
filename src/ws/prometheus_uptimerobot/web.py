import argparse
import logging
import os
import os.path
import prometheus_client
import prometheus_client.core
import requests
import sys
import time
import wsgiref.handlers
import wsgiref.simple_server

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

log = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'


class Gauge(prometheus_client.core.GaugeMetricFamily):

    NAMESPACE = 'uptimerobot'

    def __init__(self, name, documentation):
        super(Gauge, self).__init__(
            '%s_%s' % (self.NAMESPACE, name), documentation, labels=['monitor_name', 'monitor_type', 'monitor_url'])
        self._name = name

    def clone(self):
        return type(self)(self._name, self.documentation)


class UptimeRobotCollector(object):

    # Documentation: https://uptimerobot.com/api
    API_URL = 'https://api.uptimerobot.com/v2'
    STATUS_UP = 2
    MONITOR_TYPES = {
        1: 'http',
        2: 'http keyword',
        3: 'ping',
        4: 'port',
    }

    def configure(self, config_file):
        config = ConfigParser()
        config.read(os.path.expanduser(config_file))
        get = lambda x: config.get('default', x)  # noqa
        self.api_key = get('api_key')

    METRICS = {
        'up': Gauge('up', 'Is the monitor up?'),
        'status': Gauge('status', 'Numeric status of the monitor'),
        'responsetime': Gauge(
            'responsetime', 'Most recent monitor responsetime'),
        'ssl': Gauge('ssl_expire', 'Date of cert expiration'),
        'scrape_duration_seconds': Gauge(
            'scrape_duration_seconds', 'Duration of uptimerobot.com scrape'),
    }

    def describe(self):
        return self.METRICS.values()

    def collect(self):
        try:
            start = time.time()
            # Use a separate instance for each scrape request, to prevent
            # race conditions with simultaneous scrapes.
            metrics = {
                key: value.clone() for key, value in self.METRICS.items()}
            monitors = self._get_monitors()
            for monitor in monitors:
                labels_values = [monitor['friendly_name'], self.MONITOR_TYPES[monitor['type']], monitor['url']]
                status = monitor.get('status', 1)
                metrics['up'].add_metric(labels_values, 1 if status == self.STATUS_UP else 0)
                metrics['status'].add_metric(labels_values, status)
                responsetime = monitor.get('response_times', ())
                if responsetime:
                    # milliseconds
                    responsetime = responsetime[0]['value'] / 1000.0
                    metrics['responsetime'].add_metric(labels_values, responsetime)
                ssl = monitor.get('ssl', {})
                if ssl.get('product'):
                    ssl_expire = ssl['expires']
                    metrics['ssl'].add_metric(labels_values, ssl_expire)

            metrics['scrape_duration_seconds'].add_metric([], time.time() - start)

            return metrics.values()
        except Exception:
            log.error('Error during collect', exc_info=True)
            raise

    def _get_monitors(self):
        result = []
        response = self._get_paginated(0)
        result.extend(response.get('monitors', ()))
        seen = response['pagination']['limit']
        while response['pagination']['total'] > seen:
            response = self._get_paginated(seen)
            result.extend(response.get('monitors', ()))
            seen += response['pagination']['limit']
        return result

    def _get_paginated(self, offset):
        return requests.post(self.API_URL + '/getMonitors', data={
            'api_key': self.api_key,
            'format': 'json',
            'offset': offset,
            'response_times': '1',  # enable
            'response_times_limit': '1',  # just the latest one
        }).json()


COLLECTOR = UptimeRobotCollector()
# We don't want the `process_` and `python_` metrics, we're a collector,
# not an exporter.
REGISTRY = prometheus_client.core.CollectorRegistry()
REGISTRY.register(COLLECTOR)
APP = prometheus_client.make_wsgi_app(REGISTRY)


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
    # Disable superfluous accesslog to stderr
    wsgiref.simple_server.ServerHandler.close = (
        wsgiref.simple_server.SimpleHandler.close)
    wsgiref.simple_server.make_server(
        options.host, options.port, APP).serve_forever()
