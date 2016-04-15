#!/usr/bin/python
'''
301 Web redirection via AWS API Gateway
'''
import boto3
from botocore.exceptions import ClientError

CLIENT = boto3.client('apigateway')


class Gateway(object):
    '''
    All the bits needed to create an API Gateway
    '''
    # pylint: disable=too-many-instance-attributes

    def __init__(self, base_url, target_url, prefixes):
        '''
        foo
        '''
        self.base_url = base_url
        self.target_url = target_url
        self.prefixes = prefixes

        if self.base_url.startswith('http://'):
            self.base_domain = base_url.split('http://')[1]
        elif self.base_url.startswith('https://'):
            self.base_domain = base_url.split('https://')[1]

        if self.target_url.startswith('http://'):
            self.target_domain = target_url.split('http://')[1]
        elif target_url.startswith('https://'):
            self.target_domain = target_url.split('https://')[1]

        api_description = 'Redirect ' + self.base_domain + ' to ' + self.target_url
        self.resource_path = '/'
        self.region = 'us-east-1'
        self.stage_name = 'prod'

        self.certificate_name = self.base_domain
        self.certificate_body = self.base_domain + '.cert'
        self.certificate_private_key = self.base_domain + '.key'
        self.certificate_chain = self.base_domain + '-chain.crt'

        self.prefixes_index = len(prefixes)

        # Create a new API Gateway.
        # Get the API ID.
        self.api_id = CLIENT.create_rest_api(name=self.base_domain,
                                             description=api_description)['id'].strip()

        # Get the resource id of the root path (/):
        self.resources = CLIENT.get_resources(restApiId=self.api_id)['items']

        self.resource_id = []

    def method_response(self):
        '''
        Set the GET response
        '''
        for self.resource_id in self.resources:
            try:
                # Create a GET method on the root resource:
                CLIENT.put_method(restApiId=self.api_id,
                                  resourceId=self.resource_id[
                                      'id'],
                                  httpMethod='GET',
                                  apiKeyRequired=False,
                                  authorizationType='NONE')
                # Add a Method Response for status 301
                # with a required Location HTTP header:
                CLIENT.put_method_response(restApiId=self.api_id,
                                           resourceId=self.resource_id[
                                               'id'],
                                           httpMethod='GET',
                                           statusCode='301',
                                           responseModels={
                                               "application/json": "Empty"},
                                           responseParameters={"method.response.header.Location":
                                                               True})

            except IndexError as error:
                print "\033[1;31m%s\033[1;0m" % error
            except TypeError as error:
                print "\033[1;31m%s\033[1;0m" % error
            except NameError as error:
                print "\033[1;31m%s\033[1;0m" % error

    def mock(self):
        '''
        Set the GET method integration to MOCK
        with a default 301 status code.
        By using a mock integration, we do not need a back end.
        '''
        CLIENT.put_integration(restApiId=self.api_id,
                               resourceId=self.resource_id['id'],
                               httpMethod='GET',
                               type='MOCK',
                               requestTemplates={"application/json": "{\"statusCode\": 301}"})

    def integration_response(self):
        '''
        Add an Integration Response for GET method status 301.
        Set the Location header to the redirect target URL.
        '''
        CLIENT.put_integration_response(restApiId=self.api_id,
                                        resourceId=self.resource_id[
                                            'id'],
                                        httpMethod='GET',
                                        statusCode='301',
                                        responseTemplates={
                                            "application/json": "redirect"},
                                        responseParameters={"method.response.header.Location":
                                                            "'" + self.target_url + "'"})

    def deployment(self):
        '''
        Create API Gateway Deployment and Stage
        '''
        CLIENT.create_deployment(restApiId=self.api_id,
                                 description=self.base_domain + ' deployment',
                                 stageName=self.stage_name,
                                 stageDescription=self.base_domain + self.stage_name,
                                 cacheClusterEnabled=True,
                                 cacheClusterSize='0.5')

        # Print out the destination URL to use:
        print 'AWS /> Test the redirect with the following URL: '
        print 'AWS /> https://' + self.api_id + '.execute-api.' + self.region + \
              '.amazonaws.com' + '/' + self.stage_name + self.resource_path

        print 'AWS /> After testing, add an alias record for ' + self.base_domain
        print 'AWS /> pointing to the CloudFront distribution associated'
        print 'AWS /> with the API Gateway Domain Name.'

    def distribution(self):
        '''
        Create API Gateway Domain Name.
        The API Gateway Domain Name seems to be a CloudFront
        distribution with an SSL Certificate,
        Although, it will not show up in normal CloudFront queries.
        '''
        # Open and read into memory
        cert_body = open(self.certificate_body, 'r').read()
        cert_key = open(self.certificate_private_key, 'r').read()
        cert_chain = open(self.certificate_chain, 'r').read()

        try:
            CLIENT.create_domain_name(domainName=self.base_domain,
                                      certificateName=self.certificate_name,
                                      certificateBody=cert_body,
                                      certificatePrivateKey=cert_key,
                                      certificateChain=cert_chain)

            get_distribution_domain = CLIENT.get_domain_name(
                domainName=self.base_domain)

            print 'AWS /> Cloudfront domain to alias in Route 53: %s' \
                % get_distribution_domain["distributionDomainName"]

            CLIENT.create_base_path_mapping(domainName=self.base_domain,
                                            restApiId=self.api_id,
                                            stage=self.stage_name)
        except IndexError as error:
            print "\033[1;31m%s\033[1;0m" % error
        except TypeError as error:
            print "\033[1;31m%s\033[1;0m" % error
        except NameError as error:
            print "\033[1;31m%s\033[1;0m" % error
        except ClientError as error:
            print "\033[1;31m%s\033[1;0m" % error

        if self.prefixes_index > 0:
            # Do the same for the prefixes
            for prefix in self.prefixes.split():
                try:
                    prefix_domain = prefix + '.' + self.base_domain
                    CLIENT.create_domain_name(domainName=prefix_domain,
                                              certificateName=self.certificate_name,
                                              certificateBody=cert_body,
                                              certificatePrivateKey=cert_key,
                                              certificateChain=cert_chain)

                    CLIENT.get_domain_name(domainName=prefix_domain)

                    print 'AWS /> Add %s as a CNAME to %s in Route 53' \
                        % (prefix_domain, self.base_domain)

                    CLIENT.create_base_path_mapping(
                        domainName=prefix_domain, restApiId=self.api_id, stage=self.stage_name)

                except IndexError as error:
                    print "\033[1;31m%s\033[1;0m" % error
                except TypeError as error:
                    print "\033[1;31m%s\033[1;0m" % error
                except NameError as error:
                    print "\033[1;31m%s\033[1;0m" % error
                except ClientError as error:
                    print "\033[1;31m%s\033[1;0m" % error

if __name__ == "__main__":
    BASE_URL = raw_input('Enter the source URL: ')
    TARGET_URL = raw_input('Enter the destination URL: ')
    PREFIXES = raw_input(
        'Enter space seperated URL prefixes(e.g: www www2): ')

    CREATE_GW = Gateway(BASE_URL, TARGET_URL, PREFIXES)

    CREATE_METHOD = CREATE_GW.method_response()
    CREATE_MOCK = CREATE_GW.mock()
    CREATE_INTEGRATION_RESPONSE = CREATE_GW.integration_response()
    CREATE_DEPLOYMENT = CREATE_GW.deployment()
    CREATE_DISTRIBUTION = CREATE_GW.distribution()

    print 'AWS /> Please wait 10-20 minutes while ' + \
          'the CloudFront distribution is deployed ' + \
          'to all edge nodes.'
