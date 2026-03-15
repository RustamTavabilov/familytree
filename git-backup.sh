#!/bin/bash
cd /var/services/homes/tavabilovrr/familytree
git add .
git commit -m "Автоматический бэкап $(date '+%Y-%m-%d %H:%M:%S')"
git push origin master
