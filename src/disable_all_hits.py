import boto3, dotenv, os
import datetime

region_name = 'us-east-1'
dotenv.load_dotenv()
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# 1. Set up MTurk client (live endpoint)
mturk = boto3.client(
    'mturk',
    region_name='us-east-1',
    endpoint_url='https://mturk-requester.us-east-1.amazonaws.com',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
    # use sandbox for testing: 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
)

# get account balance
user_balance = mturk.get_account_balance()['AvailableBalance']
print("Your account balance is: " + user_balance)

# 2. Get all HITs
all_hits = []
response = mturk.list_hits(MaxResults=100)
all_hits.extend(response['HITs'])

while 'NextToken' in response:
    response = mturk.list_hits(MaxResults=100, NextToken=response['NextToken'])
    all_hits.extend(response['HITs'])

print(f"Found {len(all_hits)} HITs.")

# 3. Expire all HITs (set expiration to now)
for hit in all_hits:
    hit_id = hit['HITId']
    try:
        mturk.update_expiration_for_hit(
            HITId=hit_id,
            ExpireAt=datetime.datetime.utcnow()
        )
        print(f"Expired HIT: {hit_id}")
    except Exception as e:
        print(f"Failed to expire HIT {hit_id}: {e}")

# 4. Try to delete HITs (optional)
for hit in all_hits:
    hit_id = hit['HITId']
    try:
        mturk.delete_hit(HITId=hit_id)
        print(f"Deleted HIT: {hit_id}")
    except Exception as e:
        print(f"Could not delete HIT {hit_id}: {e}")
