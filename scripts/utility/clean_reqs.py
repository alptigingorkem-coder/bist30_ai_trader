
import os

req_file = 'requirements.txt'
with open(req_file, 'r') as f:
    lines = f.readlines()

unique_lines = set()
cleaned_lines = []

prune_list = {
    'webdriver-manager', 
    'colorlog', 
    'charset-normalizer',
    'idna', 
    'urllib3', 
    'certifi', 
    'requests' # These are deps of others usually, but requests is main. Keep requests.
}
# Keep requests, remove others if they are just deps. But pip freeze includes them.
# The user asked to remove "unused".
# I'll stick to what I decided: webdriver-manager, colorlog.
# And deduplicate.

final_reqs = []
seen = set()

ignore = {'webdriver-manager', 'colorlog'}

for line in lines:
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    
    pkg = line.split('==')[0].split('>=')[0].strip().lower()
    
    if pkg in seen:
        continue
    
    if pkg in ignore:
        continue
        
    seen.add(pkg)
    final_reqs.append(line)

final_reqs.sort()

with open(req_file, 'w') as f:
    f.write('\n'.join(final_reqs) + '\n')

print(f"Cleaned requirements.txt. Count: {len(final_reqs)}")
