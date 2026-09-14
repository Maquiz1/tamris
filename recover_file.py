import json
import re

file_lines = {}
line_pattern = re.compile(r'^(\d+): (.*)$')

with open('/home/maquiz/.gemini/antigravity-ide/brain/dcf28c20-0797-45f2-87e6-539b033386f0/.system_generated/logs/transcript_full.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        step_idx = data.get('step_index')
        # Only check steps right before my python script
        if step_idx in [1177, 1178, 1182, 1183, 1197, 1198, 1209, 1210]:
            content = data.get('content') or data.get('tool_responses', [{}])[0].get('output', '')
            if 'File Path: `file:///home/maquiz/projects/tamris/backend/users/templates/users/onboarding.html`' in content:
                for c_line in content.split('\n'):
                    match = line_pattern.match(c_line)
                    if match:
                        line_num = int(match.group(1))
                        text = match.group(2)
                        file_lines[line_num] = text

print(f"Recovered {len(file_lines)} lines.")
max_line = max(file_lines.keys()) if file_lines else 0
print(f"Max line: {max_line}")

if file_lines:
    with open('recovered_onboarding.html', 'w') as out:
        for i in range(1, max_line + 1):
            out.write(file_lines.get(i, f"<!-- MISSING LINE {i} -->") + '\n')
