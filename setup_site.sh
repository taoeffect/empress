#!/bin/sh -e
./.env/bin/ansible-playbook "$@" site.yml
./.env/bin/ansible-playbook -v "$@" migration.yml
