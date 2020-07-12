# Django Page Builder
Frontend page builder for Django

## Quick start
1. Add "page_builder" to your INSTALLED_APPS setting like this::

> INSTALLED_APPS = [ ... 'page_builder', ]

2. Include the page_builder URLconf in your project urls.py like this::

> path('', include('page_builder.urls')), path('page-builder/', include('page_builder.dashboard.urls')),

3. Run python manage.py migrate to create the page_builder models.

4. Start the development server and visit http://127.0.0.1:8000/page-builder/ to create a page.

5. Visit http://127.0.0.1:8000/<slug>/ to see your new page.
