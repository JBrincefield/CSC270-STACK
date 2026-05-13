#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

#home page
#reviews page
#about us page
#hotdogs vs sausages page

# make a hotdog website:


# Set up a sample application on your chosen solution stack
# Sample App
# Your sample application isn't required to have full-stack features at this point, but it may if you wish to work ahead.
# Should have at least 2-3 working static pages
# Pages should be styled with CSS (feel free to pull in libraries like Bootstrap, Tailwind, etc.)
# Each page should have content (a couple paragraphs of text and an image at a minimum, but add whatever you like.)
# Example Pages
# Home Page - Basic information/landing page about your chosen stack
# About The Team - Include a short bio and pic of each team member
# Contact Us - A non-functioning web form that take some user information

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackApp.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
