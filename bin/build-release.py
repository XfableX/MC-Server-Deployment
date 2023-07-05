import boto3
import argparse
import os
import yaml
import tarfile
import glob

parser = argparse.ArgumentParser(description="Create a release for MC")
parser.add_argument("-r", "--release-name", required=True)

args = parser.parse_args()

release_bucket = "fablemc-artifacts"
release_prefix = os.path.join("MC-Server-deployment/",args.release_name)

session = boto3.Session(region_name='ap-southeast-2')
s3 = session.client("s3")
cfn = session.client("cloudformation")

def s3_put_object(key, body):
    payload = {
        "Bucket": release_bucket,
        "Key": key,
        "Body": body
    }
    print(payload)
    s3.put_object(**payload)
print(session.get_credentials())
print(session.available_profiles)

artifact_filename = "ansible_bootstrap.tar.gz"
local_artifact_filename = os.path.join("/tmp/",artifact_filename)

with tarfile.open(local_artifact_filename, "w:gz") as artifact:
    artifact.add('Ansible')

s3_put_object(os.path.join(release_prefix,artifact_filename), local_artifact_filename)

bin_filename = "bin.tar.gz"
local_bin_filename = os.path.join("/tmp/",bin_filename)

with tarfile.open(local_bin_filename, "w:gz") as artifact:
    artifact.add('bin')
print(os.path.join(release_prefix, bin_filename))
s3_put_object(os.path.join(release_prefix, bin_filename),local_bin_filename)

for template in glob.glob("Cloudformation/*"):
    s3_put_object(os.path.join(release_prefix, "templates", os.path.basename(template)), open(template, "rb"))