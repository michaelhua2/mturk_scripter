
import os, sys, ipdb, argparse, json
from tqdm import tqdm
import numpy as np
import boto3
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
from my_hit_launcher import environments, region_name
import dominate, dotenv
from dominate.tags import *

dotenv.load_dotenv()
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

config = json.load(open('config.json', 'r'))

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=str)
    parser.add_argument('--env_type', type=str, default='sandbox', choices=['sandbox','live'])
    parser.add_argument('--results_json', type=str)
    args = parser.parse_args()

    mturk_environment = environments[args.env_type]

    client = boto3.client('mturk',
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key = aws_secret_access_key,
        region_name= region_name,
        endpoint_url=mturk_environment["endpoint"]
    )
    with open(os.path.join(args.folder,f'hit_ids_{args.env_type}.txt'),'r') as f:
        hit_ids = f.readlines()
        hit_ids = [x.strip() for x in hit_ids]
    outf = open(os.path.join(args.folder,'results.txt'),'w')

    count_total = 1e-10
    d_out = {'l_counts': [], 'l_comments': []}
    ours = config['ours']
    baselines = config['other_methods']
    for baseline in baselines:
        d_out[f"{ours}_vs_{baseline}"] = {}
        for i in range(50):
            for seed in range(5):
                d_out[f"{ours}_vs_{baseline}"][f"{i}_{seed}_"] = {'raw': []}

    for hit_id in tqdm(hit_ids):
        hit = client.get_hit(HITId=hit_id)
        
        response = client.list_assignments_for_hit(HITId=hit_id, AssignmentStatuses=['Submitted', 'Approved'])
        assignments = response['Assignments']
        print('Hit {} status: {}, num_asignments={}'.format(hit_id, hit['HIT']['HITStatus'], len(assignments)))
        # pdb.set_trace()
        namespace = {'ns': 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionFormAnswers.xsd'}
        for assign_idx, assignment in enumerate(assignments):
            root = ET.fromstring(assignment['Answer'])
            num_practice_incorrect = 0
            for answer in root.findall('ns:Answer', namespace):
                identifier = answer.find('ns:QuestionIdentifier', namespace).text
                free_text = answer.find('ns:FreeText', namespace).text
                outf.write(f"{hit_id},{identifier},{free_text}\n")
                if "selection" in identifier:
                    mode = free_text.split(",")[0]  
                    if mode == "practice":                      
                        answer = free_text.split(",")[1]
                        url_left = free_text.split(",")[2]
                        url_right = free_text.split(",")[3]
                    else:
                        mode = "test"
                        # answer = free_text.split(",")[0]
                        # url_left = free_text.split(",")[1]
                        # url_right = free_text.split(",")[2]
                        answer = free_text.split(",")[1]
                        url_left = free_text.split(",")[2]
                        url_right = free_text.split(",")[3]

                    if mode == "practice":
                        is_correct = free_text.split(",")[4]
                        if is_correct == "false":
                            num_practice_incorrect += 1
                            if num_practice_incorrect > 1:
                                break
                        continue
                    
                    assert mode == "test"
                    count_total += 1
                    method_left = url_left.split("/")[-3]
                    method_right = url_right.split("/")[-3]

                    ours_preferred = 0
                    if method_left == ours:
                        other_method = method_right
                        if answer=="left":
                            ours_preferred = 1
                    if method_right == ours:
                        other_method = method_left
                        if answer=="right":
                            ours_preferred = 1
                    
                    if ours_preferred: d_out['l_counts'].append(1)
                    else: d_out['l_counts'].append(0)

                    idx_seed = url_right.split("/")[-1].split(".")[0]
                    comparison_name = f"{ours}_vs_{other_method}"
                    d_out[comparison_name][idx_seed]['raw'].append(ours_preferred)
                if "comments" in identifier:
                    d_out['l_comments'].append(free_text)

    
    print(f"Total: {count_total}")
    print(f"Percentage: {np.mean(d_out['l_counts'])*100}% ")

    for comparison in d_out.keys():
        if comparison == 'l_counts' or comparison == 'l_comments':
            continue
        for k in d_out[comparison].keys():
            d_out[comparison][k]['mean'] = np.mean(d_out[comparison][k]['raw']) if len(d_out[comparison][k]['raw']) > 0 else 0
            # print(f"{comparison} {k}: {d_out[comparison][k]}")
        d_out[comparison]['mean'] = np.mean([d_out[comparison][k]['mean'] for k in d_out[comparison].keys()])
        print(f"{comparison}: {d_out[comparison]['mean']*100}% ")

    with open(os.path.join(args.results_json),'w') as outf:
        json.dump(d_out, outf, indent=4)

