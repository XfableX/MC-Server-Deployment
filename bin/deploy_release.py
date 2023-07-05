import boto3
import argparse
import os
import yaml
import tarfile
import threading

from botocore.exceptions import ClientError

parser = argparse.ArgumentParser(description="Create a release for MC")
parser.add_argument("-r", "--release-name", required=True)
parser.add_argument("-a", "--ami-id", required=True)
parser.add_argument("-t", "--template", required=True)

args = parser.parse_args()

release_bucket = "fablemc-artifacts"
release_prefix = os.path.join("MC-Server-deployment/",args.release_name)
s3_release_url = "s3://{0}/{1}".format(release_bucket, release_prefix)

template_vars = {
    "AMI": args.ami_id,
    "release": args.release_name
}

session = boto3.Session(region_name='ap-southeast-2')
s3 = session.client("s3")
cfn = session.client("cloudformation")

def stack_exists(stack_name):
    paginator = cfn.get_paginator("list_stacks")

    for page in paginator.paginate():
        for stack in page["StackSummaries"]:
            if stack["StackStatus"] == 'DELETE_COMPLETE':
                continue
            if stack_name == stack["StackName"]:
                return True
    return False
def deploy_stack(cf_stack_name, s3_url):
    cf_stack_template_s3_url = "{0}/templates/{1}".format(s3_release_url, cf_stack_name)

    cf_payload = {
        "StackName":cf_stack_name,
        "TemplateURL": cf_stack_template_s3_url,
        "Parameters": template_vars,
    }

    try:
        if stack_exists(cf_stack_name):
            print("INFO: UPDATING {0}".format(cf_stack_name))

            try:
                stack_result = cfn.update_stack(**cf_payload)

            except ClientError as e:
                if "No updates are to be performed" in str(e):
                    print("No updates for {0}".format(cf_stack_name))
                    return
                else:
                    raise e
            waiter = cfn.get_waiter("stack_update_complete")
        else:
            print("INFO: Creating {0}".format(cf_stack_name))
            stack_result = cfn.create_stack(**cf_payload)
            waiter = cfn.get_waiter("stack_create_complete")
        print("Waiting for {0} to be ready".format(cf_stack_name))
        waiter.wait(stackname=cf_stack_name)
    except Exception as e:
        raise e
    
deploy_stack(args.template, s3_release_url)