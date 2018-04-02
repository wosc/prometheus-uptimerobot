import json
import mock
import pkg_resources
import pytest
import werkzeug.test
import werkzeug.wrappers
import ws.prometheus_uptimerobot.web


@pytest.fixture
def fake_response():
    with mock.patch(
            'ws.prometheus_uptimerobot.web.UptimeRobotCollector'
            '._get_paginated') as page:
        page.return_value = json.loads(pkg_resources.resource_string(
            __name__, 'response.json').decode('utf-8'))
        yield page


@pytest.fixture
def testbrowser():
    return werkzeug.test.Client(
        ws.prometheus_uptimerobot.web.APP, werkzeug.wrappers.BaseResponse)


def test_converts_api_data_to_metrics(fake_response, testbrowser):
    metrics = testbrowser.get('/').data.decode('utf-8')
    ping_labels = ('{monitor_name="host ping",monitor_type="ping"'
                   ',monitor_url="example.com"}')
    assert 'uptimerobot_status%s 2.0' % ping_labels in metrics
    assert 'uptimerobot_up%s 1.0' % ping_labels in metrics
    assert 'uptimerobot_responsetime%s 0.125' % ping_labels in metrics

    assert 'monitor_name="example.com"' in metrics
    assert 'monitor_name="IMAP"' in metrics
    assert 'monitor_name="SMTP"' in metrics

    assert fake_response.call_args_list == [mock.call(0), mock.call(50)]
