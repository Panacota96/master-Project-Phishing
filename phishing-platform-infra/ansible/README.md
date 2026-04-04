# Ansible Deployment

This optional playbook provisions a VM and deploys the Flask app with Gunicorn + Nginx.

## Prerequisites
- A VM reachable over SSH
- Python and Ansible installed locally

## Setup
1. Edit `phishing-platform-infra/ansible/inventory/hosts.ini` with your server IP and SSH user.
2. Edit `phishing-platform-infra/ansible/group_vars/all.yml` with repo URL and environment variables.

## Provision
```bash
ansible-playbook -i phishing-platform-infra/ansible/inventory/hosts.ini phishing-platform-infra/ansible/playbooks/provision.yml
```

## Deploy
```bash
ansible-playbook -i phishing-platform-infra/ansible/inventory/hosts.ini phishing-platform-infra/ansible/playbooks/deploy.yml
```

## Notes
- The systemd service is `phishing-app`.
- Nginx proxies to `127.0.0.1:{{ app_port }}`.
- Update `data/quizzes.json` and run `python seed_dynamodb.py` to seed quizzes.
