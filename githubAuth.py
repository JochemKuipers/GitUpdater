from github import Github
from github import Auth
from datetime import datetime

# First create a Github instance:
auth = Auth.Token("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")
g = Github(auth=auth)

g.get_user().login

repo = g.get_repo("Hydr8gon/NooDS")

dld = repo.get_latest_release()

timezone = datetime.now().astimezone().tzinfo

print(timezone)

for asset in dld.get_assets():
    print(asset.name + " " + str(asset.size) + " " + asset.browser_download_url + " " + dld.created_at.astimezone(timezone).strftime("%Y-%m-%d %H:%M:%S"))