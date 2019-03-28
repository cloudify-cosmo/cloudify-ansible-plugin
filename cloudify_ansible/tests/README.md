# Troubleshooting

On a manager it is helpful to use this shell script for troubleshooting:

```shell
docker exec -i -t {0} /bin/bash # Skip this line if you are not using a manager in a Docker container.
sudo su
source /opt/mgmtworker/env/bin/activate
python
import sys
from os import environ
environ['ANSIBLE_HOST_KEY_CHECKING'] = "False"
sys.path.insert(0, '/opt/mgmtworker/env/plugins/default_tenant/cloudify-ansible-plugin-{0}/lib/python2.7/site-packages') # replace {0} with the current version.
import cloudify_ansible_sdk
cloudify_ansible_sdk.AnsiblePlaybookFromFile('/tmp/{0}/playbook/playbook.yaml', '/tmp/{0}/playbook/hosts').execute() # replace the {0} with the tmp folder of your execution.
```
