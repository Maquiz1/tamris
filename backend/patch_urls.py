def update_urls(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Replace both URL patterns
    import re
    content = re.sub(r"path\('apply/listing/<int:pk>/', views\.medicine_listing_apply_view, name='apply_listing'\),\n\s*path\('apply/category-ii/<int:pk>/', views\.medicine_category_ii_apply_view, name='apply_category_ii'\),", "path('apply/master/<int:pk>/', views.medicine_master_apply_view, name='apply_master'),", content)

    with open(filename, 'w') as f:
        f.write(content)

update_urls('medicines/urls.py')
