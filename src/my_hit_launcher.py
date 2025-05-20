import os, sys, pdb, argparse, dotenv
from glob import glob
import boto3

environments = {
    "live": {
        "endpoint": "https://mturk-requester.us-east-1.amazonaws.com",
        "preview": "https://www.mturk.com/mturk/preview",
        "manage": "https://requester.mturk.com/mturk/manageHITs",
        "reward": "0.25"
    },
    "sandbox": {
        "endpoint": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
        "preview": "https://workersandbox.mturk.com/mturk/preview",
        "manage": "https://requestersandbox.mturk.com/mturk/manageHITs",
        "reward": "0.25"
    },
}
region_name = 'us-east-1'

dotenv.load_dotenv()
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=str)
    parser.add_argument('--env_type', type=str, default='sandbox', choices=['sandbox','live'])
    args = parser.parse_args()
    
    mturk_environment = environments[args.env_type]

    client = boto3.client('mturk',
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key = aws_secret_access_key,
        region_name= region_name,
        endpoint_url=mturk_environment["endpoint"]
    )
    user_balance = client.get_account_balance()['AvailableBalance']
    print("Your account balance is: " + user_balance)

    outf_hit = open(os.path.join(args.folder,f'hit_ids_{args.env_type}.txt'),'w')

    # load all the html files
    for idx, f in enumerate(sorted(glob(os.path.join(args.folder,'htmls','*.html')))):
        if not idx:
            print(f)
        html_file = open(f, 'r').read()
        # see these for more details on the qualification requirements
        # https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs 
        if args.env_type=="live":
            worker_requirements = [
                {
                    'QualificationTypeId': '000000000000000000L0',
                    'Comparator': 'GreaterThanOrEqualTo',
                    'IntegerValues': [90],
                    'RequiredToPreview': True,
                },
                {
                    "QualificationTypeId":"00000000000000000071",
                    "Comparator":"EqualTo",
                    "LocaleValues":[{"Country":"US"}]
                },
                # min number of tasks completed = 1000
                {
                    "QualificationTypeId":"00000000000000000040",
                    "Comparator":"GreaterThanOrEqualTo",
                    'IntegerValues': [1000],
                },
            ]
        else:
            worker_requirements = []
        # Create the HIT
        response = client.create_hit(
            MaxAssignments=5,
            LifetimeInSeconds=10_000,
            AssignmentDurationInSeconds=600,
            Reward=mturk_environment['reward'],
            Title=f'Answer simple question about images, - {idx}',
            Keywords='images, quality, machine learning',
            Description=f'Answer simple question about images, - {idx}',
            Question=html_file,
            QualificationRequirements=worker_requirements,
        )
        hit_id = response['HIT']['HITId']
        outf_hit.write(f'{hit_id}\n')
        print("You can work the HIT here:")
        print(mturk_environment['preview'] + "?groupId={}".format(response['HIT']['HITTypeId']))
        if args.env_type=="sandbox":
            # only do 1 run for sandbox
            break
    outf_hit.close()


