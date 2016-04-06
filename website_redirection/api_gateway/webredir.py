#!/usr/bin/python
'''
Web redirection via AWS API Gateway
Sourced from: https://alestic.com/2015/11/amazon-api-gateway-aws-cli-redirect/
'''
import boto3
from botocore.exceptions import ClientError

CLIENT = boto3.client('apigateway')

BASE_URL = raw_input('Enter the source URL: ')
TARGET_URL = raw_input('Enter the destination URL: ')

BASE_DOMAIN = BASE_URL.split('https://')[1]
TARGET_DOMAIN = TARGET_URL.split('https://')[1]

API_DESCRIPTION = 'Redirect ' + BASE_DOMAIN + ' to ' + TARGET_URL
RESOURCE_PATH = '/'
REGION = 'us-east-1'
STAGE_NAME = 'prod'

CERTIFICATE_NAME = BASE_DOMAIN
CERTIFICATE_BODY = BASE_DOMAIN + '.cert'
CERTIFICATE_PRIVATE_KEY = BASE_DOMAIN + '.key'
CERTIFICATE_CHAIN = BASE_DOMAIN + '-chain.crt'

# 1. Create a new API Gateway.
# 2. Get the API ID.
API_ID = CLIENT.create_rest_api(name=BASE_DOMAIN,
                                description=API_DESCRIPTION)['id'].strip()

# 1. Get the resource id of the root path (/):
RESOURCES = CLIENT.get_resources(restApiId=API_ID)['items']

for resource_id in RESOURCES:
    try:
        # Create a GET method on the root resource:
        CREATE_GET_METHOD = CLIENT.put_method(restApiId=API_ID,
                                              resourceId=resource_id['id'],
                                              httpMethod='GET',
                                              apiKeyRequired=False,
                                              authorizationType='NONE')
        # Add a Method Response for status 301
        # with a required Location HTTP header:
        ADD_METHOD_RESPONSE = CLIENT.put_method_response(restApiId=API_ID,
                                                         resourceId=resource_id['id'],
                                                         httpMethod='GET',
                                                         statusCode='301',
                                                         responseModels={"application/json":"Empty"},
                                                         responseParameters={"method.response.header.Location":True})

        # Set the GET method integration to MOCK
        # with a default 301 status code.
        # By using a mock integration, we do not need a back end.
        SET_MOCK = CLIENT.put_integration(restApiId=API_ID,
                                          resourceId=resource_id['id'],
                                          httpMethod='GET',
                                          type='MOCK',
                                          requestTemplates={"application/json":"{\"statusCode\": 301}"})

        # Add an Integration Response for GET method status 301.
        # Set the Location header to the redirect target URL.
        ADD_INTEGRATION_RESPONSE = CLIENT.put_integration_response(restApiId=API_ID,
                                                                   resourceId=resource_id['id'],
                                                                   httpMethod='GET',
                                                                   statusCode='301',
                                                                   responseTemplates={"application/json":"redirect"},
                                                                   responseParameters={"method.response.header.Location":"'" + TARGET_URL + "'"})

    except TypeError as error:
        print error
    except NameError as error:
        print error


try:
    # Create API Gateway Deployment and Stage
    CREATE_DEPLOYMENT = CLIENT.create_deployment(restApiId=API_ID,
                                                 description=BASE_DOMAIN + 'deployment',
                                                 stageName=STAGE_NAME,
                                                 stageDescription=BASE_DOMAIN + STAGE_NAME,
                                                 cacheClusterEnabled=True,
                                                 cacheClusterSize='0.5')

    # Create API Gateway Domain Name.
    # The API Gateway Domain Name seems to be a CloudFront
    # distribution with an SSL Certificate,
    # Although, it will not show up in normal CloudFront queries.

    # Print out the destination URL to use:
    print '## Test the redirect with the following URL: '
    print '## https://' + API_ID + '.execute-api.' + REGION + \
          '.amazonaws.com' + '/' + STAGE_NAME + RESOURCE_PATH

    print '## The above is a CloudFront URL.'
    print '## After testing, add an alias record for ' + BASE_DOMAIN
    print '## pointing to the CloudFront distribution associated'
    print '## with the API Gateway Domain Name.'

    CREATE_DISTRIBUTION_DOMAIN = CLIENT.create_domain_name(domainName=BASE_DOMAIN,
                                                           certificateName=CERTIFICATE_NAME,
                                                           certificateBody='file://' + CERTIFICATE_BODY,
                                                           certificatePrivateKey='file://' + CERTIFICATE_PRIVATE_KEY,
                                                           certificateChain='file://' + CERTIFICATE_CHAIN)

    CREATE_BASE_PATH_MAP = CLIENT.create_base_path_mapping(domainName=BASE_DOMAIN,
                                                           restApiId=API_ID,
                                                           stage=STAGE_NAME)
except TypeError as error:
    print error
except NameError as error:
    print error
except ClientError as error:
    print error

print '## Please wait 10-20 minutes while the CloudFront distribution is deployed to all edge nodes.'
