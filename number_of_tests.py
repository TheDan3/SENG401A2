import os

import gitlab
import re
from dotenv import load_dotenv
from pprint import pprint


def extract_scenarios(feature_content):
    # Regular expression to match 'Scenario:' followed by any text on the same line
    scenario_pattern_space = re.compile(r'\bScenario\b: (.+)')
    matches_space = scenario_pattern_space.findall(feature_content)

    if matches_space:
        return [description.strip() for description in matches_space]

    # If no matches with space, try without space
    scenario_pattern_no_space = re.compile(r'\bScenario\b:(.+)')
    matches_no_space = scenario_pattern_no_space.findall(feature_content)

    if matches_no_space:
        return [description.strip() for description in matches_no_space]
    
    return ['']

def map_features_to_scenarios_by_tag(gitlab_url, private_token, project_id, directories, tag):
    gl = gitlab.Gitlab(gitlab_url, private_token=private_token)
    project = gl.projects.get(project_id)

    feature_scenario_mapping = {}

    for directory in directories:
        items = project.repository_tree(path=directory, recursive=True, ref=tag, get_all=True)
        feature_files = [item['path'] for item in items if item['type'] == 'blob' and item['name'].endswith('.feature')]

        feature_contents = {}
        for file_path in feature_files:
            file_content = project.files.raw(file_path=file_path, ref=tag).decode('utf-8')
            feature_contents[os.path.basename(file_path)] = file_content

        for file_name, content in feature_contents.items():
            scenarios = extract_scenarios(content)
            feature_scenario_mapping[file_name] = len(scenarios)

    return feature_scenario_mapping

def main():
    load_dotenv()

    private_token = os.getenv("TOKEN")

    gitlab_url = 'https://eng-git.canterbury.ac.nz/'
    project_id = 15303
    directories = [
        'src/test/resources/features/integration',
        'CypressTestingEnvironment/cypress/e2e'
    ]
    tag = 'sprint_6.2'

    feature_scenario_mapping = map_features_to_scenarios_by_tag(gitlab_url, private_token, project_id, directories, tag)

    pprint(feature_scenario_mapping, sort_dicts=False)

    print(sum(feature_scenario_mapping.values()))


main()

