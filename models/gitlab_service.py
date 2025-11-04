import os, gitlab, yaml, base64
from typing import Optional, Dict, Any

class GitLabService:

    def __init__(self):
        "initializing Gitlab connection"
        self.gitlab_url = os.getenv("GITLAB_URL")
        self.token = os.getenv("GITLAB_TOKEN")
        self.project_id = os.getenv("GITLAB_SOT_PROJECT_ID")
        self.default_branch = os.getenv("GITLAB_SOT_BRANCH", "main")

        if not all([self.gitlab_url, self.token, self.project_id]):
            raise ValueError("Missing GitLab environment variables")
        
        # Connect to GitLab
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.token)
        self.project = self.gl.projects.get(self.project_id)
        
        print(f"✓ GitLab service connected to project: {self.project.name}")


    def read_sot_yaml(self, file_path, branch):
        with open (file_path, 'r') as f:
            yaml_dict = yaml.safe_load(f)
            return yaml_dict
      
