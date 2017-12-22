#!/usr/bin/python

"""
Pushes nVidia GPU metrics to a Prometheus Push gateway for later collection.
"""

import argparse
import logging
import time
import platform

import socket
import os
import urllib2
import json
import importlib

from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway
from prometheus_client import start_http_server, core
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

import CryptoAPICollector

log = logging.getLogger('crypto-api')

def _create_parser():
	parser = argparse.ArgumentParser(description='Crypto API exporter')
	parser.add_argument('--verbose',
						help='Turn on verbose logging',
						action='store_true')

	parser.add_argument('-u', '--update-period',
						help='Period between calls to update metrics, '
							 'in seconds. Defaults to 30.',
						default=30)

	parser.add_argument('-g', '--gateway',
						help='If defined, gateway to push metrics to. Should '
							 'be in the form of <host>:<port>.',
						default=None)

	parser.add_argument('-cp', '--collector-port',
						help='If non-zero, port to run the collector http server',
						type=int,
						default=0)
	return parser

def collect(args):
	REGISTRY.register(CryptoAPICollector.CryptoAPICollector("ETH", "http://api.ethermine.org"))
	REGISTRY.register(CryptoAPICollector.CryptoAPICollector("ZEC", "http://api-zcash.flypool.org"))

	if args.collector_port:
		log.debug('starting http server on port %d', args.collector_port)
		start_http_server(args.collector_port)
		log.info('HTTP server started on port %d', args.collector_port)

	while True:
		if args.gateway:
			log.debug('pushing metrics to gateway at %s...', args.gateway)
			hostname = platform.node()
			push_to_gateway(args.gateway, job=hostname, registry=REGISTRY)
			log.debug('push complete.')

		time.sleep(args.update_period)

def main():
	parser = _create_parser()
	args = parser.parse_args()
	logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

	try:
		pid = os.fork()

		if ( pid == 0 ):
			log.info('collect as a child process %d'%os.getpid())
			collect(args)

		while True:
			time.sleep(1)

	except Exception as e:
		log.error('Exception thrown - %s', e, exc_info=True)   

if __name__ == '__main__':
	main()
