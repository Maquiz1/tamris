import re
import glob

def fix_file(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # The pattern is <div class="row g-3 mb-4 border p-3 bg-light rounded">
    # We want to change it to:
    # <div class="mb-4 border p-3 bg-light rounded">
    #     <div class="row g-3">
    
    # We also need to close the inner <div class="row g-3"> before the outer div closes.
    # Since it's a bit complex with regex to find the closing tag properly, let's use a simpler approach.
    
    # Let's replace the opening tag
    pattern = r'<div class="(row[^"]*? border p-3 bg-light rounded)">'
    # Actually, it's safer to just replace `<div class="row g-3 mb-4 border p-3 bg-light rounded">` 
    # with `<div class="mb-4 border p-3 bg-light rounded">\n<div class="row g-3">`
    # and then add an extra `</div>` at the end of the block.
    # But wait, there could be multiple. Let's just find them exactly.
    
    # We can do this manually for the exact occurrences.
    pass

