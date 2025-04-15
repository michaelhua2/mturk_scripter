
import os, sys, ipdb, argparse
from tqdm import tqdm
import numpy as np
import boto3
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
from my_hit_launcher import environments, region_name
import dominate
from dominate.tags import *


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=str)
    parser.add_argument('--env_type', type=str, default='sandbox', choices=['sandbox','live'])
    args = parser.parse_args()

    mturk_environment = environments[args.env_type]

    client = boto3.client('mturk',
        aws_access_key_id = "ACCESS_KEY",
        aws_secret_access_key = "SECRET_KEY",
        region_name= region_name,
        endpoint_url=mturk_environment["endpoint"]
    )
    with open(os.path.join(args.folder,f'hit_ids_{args.env_type}.txt'),'r') as f:
        hit_ids = f.readlines()
        hit_ids = [x.strip() for x in hit_ids]
    outf = open(os.path.join(args.folder,'results.txt'),'w')

    l_counts = []
    count_total = 1e-10
    d_index_to_score = {}
    d_index_to_url_a = {}
    d_index_to_url_b = {}

    for hit_id in tqdm(hit_ids):
        hit = client.get_hit(HITId=hit_id)
        
        response = client.list_assignments_for_hit(HITId=hit_id, AssignmentStatuses=['Submitted', 'Approved'])
        assignments = response['Assignments']
        print('Hit {} status: {}, num_asignments={}'.format(hit_id, hit['HIT']['HITStatus'], len(assignments)))
        # pdb.set_trace()
        namespace = {'ns': 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd'}
        for assignment in assignments:
            root = ET.fromstring(assignment['Answer'])
            for answer in root.findall('ns:Answer', namespace):
                identifier = answer.find('ns:QuestionIdentifier', namespace).text
                free_text = answer.find('ns:FreeText', namespace).text
                # print(f"Identifier: {identifier}, Answer: {free_text}")
                outf.write(f"{hit_id},{identifier},{free_text}\n")
                if "selection" in identifier:
                    count_total += 1
                    answer = free_text.split(",")[0]
                    url_left = free_text.split(",")[1]
                    url_right = free_text.split(",")[2]
                    

                    test_a_preferred = False
                    if answer=="left" and "testA" in url_left:
                        test_a_preferred = True
                    elif answer=="right" and "testA" in url_right:
                        test_a_preferred = True
                    
                    if test_a_preferred: l_counts.append(1)
                    else: l_counts.append(0)


                    # pdb.set_trace()
                    img_idx = int(url_right.split("/")[-1].split(".")[0])
                    if img_idx not in d_index_to_score:
                        d_index_to_score[img_idx] = [test_a_preferred]
                    else:
                        d_index_to_score[img_idx].append(test_a_preferred)
                    
                    if "testA" in url_left:
                        d_index_to_url_a[img_idx] = url_left
                        d_index_to_url_b[img_idx] = url_right
                    elif "testA" in url_right:
                        d_index_to_url_a[img_idx] = url_right
                        d_index_to_url_b[img_idx] = url_left

    print(f"Total: {count_total}")
    print(f"Percentage: {np.mean(l_counts)*100}% ")

