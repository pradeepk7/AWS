#!/usr/bin/python
'''
Deletes Rest API Service
'''
import time
import boto3

CLIENT = boto3.client('apigateway')

GET_APIS = CLIENT.get_rest_apis()['items']

for base_domain in GET_APIS:
    try:
        print "Deleting %s" % base_domain['id']
        CLIENT.delete_rest_api(restApiId=base_domain['id'])
        CLIENT.delete_domain_name(domainName=base_domain['id'])
        time.sleep(45)
    except TypeError as error:
        print error
    except NameError as error:
        print error
    except ClientError as error:
        print error
