lines = []
with open('old_lines.txt', 'r') as f:
    recording = False
    for line in f:
        # Strip line numbers
        if ':' in line:
            text = line.split(':', 1)[1][1:] # remove line num and space
        else:
            text = line
        text = text.rstrip('\n')
        
        if '{# ═══ LEFT SIDE MENU ═══ #}' in text:
            recording = True
            
        if recording:
            lines.append(text)
            
        if '{# ═══ RIGHT CONTENT ═══ #}' in text:
            recording = False
            break

# Remove the RIGHT CONTENT line itself
if lines and '{# ═══ RIGHT CONTENT ═══ #}' in lines[-1]:
    lines = lines[:-1]

with open('left_menu_extracted.html', 'w') as out:
    out.write('\n'.join(lines))
