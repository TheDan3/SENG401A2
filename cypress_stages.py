from dotenv import load_dotenv
import os
import gitlab
from dateutil import parser
import csv

load_dotenv()

private_token = os.getenv("TOKEN")

gitlab_url = 'https://eng-git.canterbury.ac.nz/'
project_id = 15303
stage_name = 'cypress'
start_tag = 'sprint_2.1'
end_tag = 'sprint_3.4'

gl = gitlab.Gitlab(gitlab_url, private_token=private_token)
project = gl.projects.get(project_id)

# Get commit dates of the tags
def get_commit_dates(tag):
    tag_data = project.tags.get(tag)
    commit_date = tag_data.commit['committed_date']
    return parser.isoparse(commit_date)

# Get pipelines between two dates
def get_pipelines_between_dates(start_date, end_date):
    pipelines = []
    page = 1

    while True:
        current_pipelines = project.pipelines.list(updated_after=start_date.isoformat(),
                                                   updated_before=end_date.isoformat(), page=page, per_page=100)
        if not current_pipelines:
            break

        pipelines.extend(current_pipelines)
        page += 1

    return pipelines

# Count stage executions for a range of pipelines and collect job details
def count_stage_executions(start_tag, end_tag):
    start_date = get_commit_dates(start_tag)
    end_date = get_commit_dates(end_tag)
    pipelines = get_pipelines_between_dates(start_date, end_date)
    total_count = 0
    passed_count = 0
    failed_count = 0
    first_job_passed = None

    print("Pipeline details between tags:")

    for pipeline in pipelines:
        print(f"Pipeline ID: {pipeline.id}, SHA: {pipeline.sha}, Status: {pipeline.status}, Created At: {pipeline.created_at}")
        jobs = pipeline.jobs.list(all=True)
        for job in jobs:
            if job.stage == stage_name:
                total_count += 1
                if job.status == 'success':
                    passed_count += 1
                    if first_job_passed is None:
                        first_job_passed = True
                elif job.status == 'failed':
                    failed_count += 1
                    if first_job_passed is None:
                        first_job_passed = False
                print(f"  Job ID: {job.id}, Status: {job.status}, Created At: {job.created_at}, Stage: {job.stage}")

    return total_count, passed_count, failed_count, first_job_passed

# Write results to a CSV file
def write_to_csv(data, filename="results.csv"):
    file_exists = os.path.isfile(filename)
    headers = ["start_tag", "end_tag", "number of runs", "number of passes", "number of fails", "first job passed"]
    with open(filename, mode='a', newline='') as file:  # Open the file in append mode
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)  # Write headers only if the file doesn't exist
        writer.writerow(data)

if __name__ == '__main__':
    total_count, passed_count, failed_count, first_job_passed = count_stage_executions(start_tag, end_tag)
    print(f'The stage "{stage_name}" was executed {total_count} times between "{start_tag}" and "{end_tag}".')
    print(f'Passed: {passed_count}')
    print(f'Failed: {failed_count}')
    print(f'First job passed: {first_job_passed}')

    data = [start_tag, end_tag, total_count, passed_count, failed_count, first_job_passed]
    write_to_csv(data)
