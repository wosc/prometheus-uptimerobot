======================================
prometheus metrics for uptimerobot.com
======================================

.. image:: https://travis-ci.org/wosc/prometheus-uptimerobot.png
   :target: https://travis-ci.org/wosc/prometheus-uptimerobot

This packages exports `Uptime Robot`_ monitor results as `Prometheus`_ metrics.

.. _`Uptime Robot`: https://uptimerobot.com
.. _`Prometheus`: https://prometheus.io


Usage
=====

Configure API key
-----------------

You'll need to provide the API key of your uptimerobot.com account using a
configuration file::

    [default]
    api_key = 123456789

See the `Uptime Robot API documentation`_ for details.


Set up HTTP service
-------------------

Then you need to set up an HTTP server, either with a dedicated process::

    $ uptimerobot_exporter --host localhost --port 9429 --config /path/to/config

or as a CGI script, if you have infrastructure for that set up anyway.
Here's an example apache configuration snippet to do this::

    ScriptAlias /metrics/uptimerobot /path/to/uptimerobot_exporter_cgi
    <Location /metrics/uptimerobot>
      SetEnv PROMETHEUS_UPTIMEROBOT_CONFIG /path/to/config
      # SetEnv PROMETHEUS_UPTIMEROBOT_LOGFILE /path/to/log  # optional, for debugging
    </Location>


Configure Prometheus
--------------------

::

    scrape_configs:
      - job_name: 'uptimerobot'
        scrape_interval: 300s
        static_configs:
          - targets: ['localhost:9429']

The following metrics are exported, each with labels ``{monitor_name="example.com",monitor_type="http",monitor_url="https://example.com"}``:

* ``uptimerobot_up`` gauge (1=up, 0=down)
* ``uptimerobot_status`` gauge
* ``uptimerobot_responsetime`` gauge

See the `Uptime Robot API documentation`_ section "Parameters" for details on
the possible ``status`` values. The ``monitor_type`` is translated from its
numeric code to one of ``http``, ``http keyword``, ``ping``, or ``port``.

Additionally, a ``uptimerobot_scrape_duration_seconds`` gauge is exported.


.. _`Uptime Robot API documentation`: https://uptimerobot.com/api
