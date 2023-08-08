import requests
import os
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, make_wsgi_app
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from flask import Flask, Response
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv('env/env.prod')
token = os.getenv("TELEGRAM_TOKEN")
server_url = os.getenv("SERVER_URL")
mistype = os.getenv("MIS_TYPE").lower()


class TelegramWebhookInfoExporter:

    def __init__(self, telegram_token):
        self.telegram_token = telegram_token
        self.counter = 0

    def fetch_webhook_info(self):
        response = requests.get(f'https://api.telegram.org/bot{self.telegram_token}/getWebhookInfo')
        if response.status_code == 200:
            info = response.json()
            self.counter += 1
            return info['result']['pending_update_count']

    def collect(self):
        pending_updates_count = GaugeMetricFamily(
            "pending_telegram_webhook_updates_count",
            "Telegram webhook pending updates count",
            labels=["client", "mis-type"]
        )

        requests_count = CounterMetricFamily(
            "total_requests_count",
            "Total requests count",
            labels=["client", "mistype"]
        )

        pending_updates_count.add_metric([server_url, mistype], self.fetch_webhook_info())
        yield pending_updates_count

        requests_count.add_metric([server_url, mistype], self.counter)
        yield requests_count


REGISTRY.register(TelegramWebhookInfoExporter(token))


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
