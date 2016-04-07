#!/usr/bin/python
'''
Deletes Rest API Service
'''
import time
import boto3
from botocore.exceptions import ClientError

CLIENT = boto3.client('apigateway')

GET_APIS = CLIENT.get_rest_apis()['items']

for base_domain in GET_APIS:
    try:
        print "Deleting %s" % base_domain['id']
        CLIENT.delete_rest_api(restApiId=base_domain['id'])
        CLIENT.delete_domain_name(domainName=base_domain['id'])
        time.sleep(45)
    except TypeError as error:
        print "\033[1;31m%s\033[1;0m" % error
    except NameError as error:
        print "\033[1;31m%s\033[1;0m" % error
    except ClientError as error:
        print "\033[1;31m%s\033[1;0m" % error

print 'AWS /> Please wait 10-20 minutes while the CloudFront distribution is removed from all edge nodes.'
