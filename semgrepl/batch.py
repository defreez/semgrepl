"""For running large Semgrepl queries using AWS Batch"""

import json
import boto3
import time
import io
import pickle
from tqdm import tqdm

def _start_jobs(name, repos, cmd, max_repos=0):
    """Starts one batch job for each repo in the list.

    Returns:
        None
    """

    batch = boto3.client('batch', region_name='us-west-2')

    jobs_to_repos = dict()
    running_jobs = set()
    counter = 0
    if not max_repos:
        max_repos = len(repos)
    print("Submitting jobs...")
    for repo in tqdm(repos[:max_repos]):
        counter += 1
        job_name = "Semgrepl-" + name + "-" + str(counter)
        command = ["/root/batch.sh", job_name, repo['repo_url'], cmd]
        response = batch.submit_job(
            jobName=job_name,
            jobQueue='SemgreplSmallQ',
            jobDefinition="Semgrepl",
            containerOverrides={'command': command}
        )
        jobs_to_repos[job_name] = repo['repo_url']
        running_jobs.add(response['jobId'])

    print()
    s3 = boto3.client('s3')
    finished_pickles = {}
    time.sleep(1)

    print("Gathering results...")
    finished_ids = set()
    num_done = 0
    pbar = tqdm(total=counter)
    while num_done < counter:
        time.sleep(1)
        for job in running_jobs.difference(finished_ids):
            response = batch.describe_jobs(jobs=[job])
            status = response['jobs'][0]['status']
            if status == 'SUCCEEDED':
                num_done += 1
                finished_job_name = response['jobs'][0]['jobName']
                finished_ids.add(job)
                pbar.update(1)

                f = io.BytesIO()
                s3.download_fileobj('semgrepl', 'pickles/{}.p'.format(finished_job_name), f)
                f.seek(0)
                p = pickle.load(f)
                finished_pickles[jobs_to_repos[finished_job_name]] = p
                f.close()

            if status == 'FAILED':
                num_done += 1
                finished_ids.add(job)
                pbar.update(1)

    pbar.close()

    return finished_pickles


def run(job_name, repos_json_file, cmd, max_jobs):
    with open(repos_json_file, 'r') as f:
        repos_json = json.load(f)
    return _start_jobs(job_name, repos_json['inputs'], cmd, max_jobs)
