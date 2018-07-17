#!/user/bin/env python
import json
import os
import requests

from collections import Counter
from elasticsearch import Elasticsearch
from operator import itemgetter

# Sentry vars
sentry_host = os.environ.get('SENTRY_HOST')
sentry_org = os.environ.get('SENTRY_ORG')
sentry_project = os.environ.get('SENTRY_PROJECT')
sentry_token = os.environ.get('SENTRY_TOKEN')

# Elasticsearch vars
es_url = os.environ.get('ES_URL')
es_username = os.environ.get('ES_USERNAME')
es_password = os.environ.get('ES_PASSWORD')
es_index = os.environ.get('ES_INDEX')
es_type = os.environ.get('ES_TYPE')
es_headers = {'content-type': 'application/json'}
es_auth = HTTPBasicAuth(es_username, es_password)
es = Elasticsearch(http_compress = True)

def post_to_elasticsearch(body, doc_id):
    """
    Post unique documents to Elastic via the API
    """
    resp = requests.post('{}/{}/{}/{}'.format(es_url, es_index, es_type, doc_id), body, headers=es_headers, params={'op_type': 'create'}, auth=es_auth)
    if resp.status_code == 201:
        print('created')
        return True
    if resp.status_code == 409:
        print('document_already_exists_exception')
        return False

def handler():
    """
    Grab sentry events, sort by ID and loop through
    """
    try:
        resp = requests.get('https://sentry.io/api/0/projects/{}/{}/events/'.format(sentry_org, sentry_project), headers={'Authorization': 'Bearer {}'.format(sentry_token)})
    except Exception as e:
        print('Error connecting to Sentry - {}'.format(e))
    else:
        events = resp.json()
        sorted_events=sorted(events, key=itemgetter('id'))
        next_url = resp.links['next']['url']
        previous_url = resp.links['previous']['url']

    for event in events:
        doc_id = event['eventID']
        if post_to_elasticsearch(event, doc_id):
            continue
        else:
            break
