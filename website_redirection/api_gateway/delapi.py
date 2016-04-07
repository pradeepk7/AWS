#!/usr/bin/python
'''
Deletes Rest API Service
'''
import time
import boto3

CLIENT = boto3.client('apigateway')

GET_APIS = CLIENT.get_rest_apis()['items']

for API_NAME in GET_APIS:
    print "Deleting %s" % API_NAME['id']
    CLIENT.delete_rest_api(restApiId=API_NAME['id'])
    CLIENT.delete_domain_name(domainName=API_NAME['id'])
    time.sleep(45)
