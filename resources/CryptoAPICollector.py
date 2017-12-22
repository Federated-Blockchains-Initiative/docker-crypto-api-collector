import logging

import requests

from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway
from prometheus_client import start_http_server, core
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY


class CryptoAPICollector(object):

	user_agent = 'python-ethapi'

	def __init__(self, currency, api_host):
		self.log = logging.getLogger("%s-exporter"%currency)
		self.currency = currency
		self.api_host = api_host
		self.prefix_s = self.currency.upper() + ' '
		self.prefix = self.currency.lower() + '_'
		self.labels	= {
			'currency': self.currency,
			'host': self.api_host
			}

	def getNetworkStats(self):
		return self.getAPIStat('networkStats')

	def getAPIStat(self, method):
		url = '/'.join([self.api_host, method])
		headers = {
			'user-agent': self.user_agent
			}
		try:
			self.log.debug('connecting to api ...')
			resp = requests.get(url, headers=headers)
			self.log.debug('parsing JSON response')
			result = resp.json()
		except Exception as e:
			self.log.info('api not available: %s', e)
			return None

		# return {
		# 	"time": 1513977298,
		# 	"blockTime": 144.34166666666667,
		# 	"difficulty": 7884304,
		# 	"hashrate": 427286248,
		# 	"usd": 520.28,
		# 	"btc": 0.03825
		# 	}
		return result['data']

	def collect(self):
		networkStats = self.getNetworkStats()

		if ( not networkStats ):
			return

		try:
			self.log.debug('Querying for clocks information...')
			network_block_time = float(networkStats['blockTime'])
			metric = GaugeMetricFamily(self.prefix + 'network_block_time', self.prefix_s + "network block time", labels=self.labels.keys())
			metric.add_metric(self.labels.values(), network_block_time)
			yield metric
			network_difficulty = float(networkStats['difficulty'])
			metric = GaugeMetricFamily(self.prefix + 'network_difficulty', self.prefix_s + "network difficulty", labels=self.labels.keys())
			metric.add_metric(self.labels.values(), network_difficulty)
			yield metric
			network_hashrate = int(networkStats['hashrate'])
			metric = GaugeMetricFamily(self.prefix + 'network_hashrate', self.prefix_s + "network hashrate", labels=self.labels.keys())
			metric.add_metric(self.labels.values(), network_hashrate)
			yield metric
			rate_usd = float(networkStats['usd'])
			metric = GaugeMetricFamily(self.prefix + 'rate_usd', self.prefix_s + "USD change rate", labels=self.labels.keys())
			metric.add_metric(self.labels.values(), rate_usd)
			yield metric
			rate_btc = float(networkStats['btc'])
			metric = GaugeMetricFamily(self.prefix + 'rate_btc', self.prefix_s + "BTC change rate", labels=self.labels.keys())
			metric.add_metric(self.labels.values(), rate_btc)
			yield metric			
			self.log.info('collected block_time:%.1fs difficulty:%.1f hashrate:%d rate_usd:%.1f rate_btc:%f', network_block_time, network_difficulty, network_hashrate, rate_usd, rate_btc)
		except Exception as e:
			self.log.warning(e, exc_info=True)