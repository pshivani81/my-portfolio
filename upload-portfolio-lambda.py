import json
import boto3
from botocore.client import Config
import StringIO
import zipfile
import mimetypes
def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic= sns.Topic('arn:aws:sns:us-east-1:061924451583:deployPortfolioTopic')
    location = {
        "bucketName":'portfoliobuild.swipartners.com',
        "objectKey" :'portfoliobuilder.zip'
            }

    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
	            if artifact["name"] == "MyAppBuild":
	               location = artifact["location"]["s3Location"]

        print "Building portfolio from "+str(location)
        s3 = boto3.resource('s3',config=Config(signature_version='s3v4'),verify=False)

        portfolio_bucket= s3.Bucket('shivaniportfolio.swipartners.com')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location["objectKey"],portfolio_zip)


        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj =  myzip.open(nm)
                print nm


        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj =  myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj,nm)
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

            topic.publish(Subject="publish",Message="sns notification success")
            print 'job done'
            if job:
             codepipeline = boto3.client('codepipeline')
             codepipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="publish",Message="sns notification failure")
