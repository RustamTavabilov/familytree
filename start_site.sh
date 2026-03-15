#!/bin/bash
sleep 10
cd /var/services/homes/tavabilovrr/familytree
/opt/bin/python3 manage.py runserver 0.0.0.0:8000 >> /var/services/homes/tavabilovrr/familytree/django.log 2>&1
