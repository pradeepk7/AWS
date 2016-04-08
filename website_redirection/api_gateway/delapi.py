#!/usr/bin/python
'''
Deletes ALL Rest API Services
'''
import time
import boto3
from botocore.exceptions import ClientError

CLIENT = boto3.client('apigateway')

GET_APIS = CLIENT.get_rest_apis()['items']

for base_domain in GET_APIS:
    try:
        print "Deleting %s - %s" % (base_domain['id'], base_domain['name'])
        BPATH = CLIENT.get_base_path_mappings(domainName=base_domain['name'])
        if BPATH is True:
            CLIENT.delete_base_path_mapping(domainName=base_domain['name'],
                                            basePath=BPATH)
        CLIENT.delete_domain_name(domainName=base_domain['name'])
        CLIENT.delete_rest_api(restApiId=base_domain['id'])
        time.sleep(60)
    except IndexError as error:
        print "\033[1;31m%s\033[1;0m" % error
    except TypeError as error:
        print "\033[1;31m%s\033[1;0m" % error
    except NameError as error:
        print "\033[1;31m%s\033[1;0m" % error
    except ClientError as error:
        print "\033[1;31m%s\033[1;0m" % error

print 'AWS /> Please wait 10-20 minutes while the CloudFront distribution is removed from all edge nodes.'
