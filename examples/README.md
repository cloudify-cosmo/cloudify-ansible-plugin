Scaleuplist Example

1. Install some vms, for example `cfy install https://github.com/cloudify-community/blueprint-examples/releases/download/latest/virtual-machine.zip -n aws.yaml -b vms`
2. Scale the VM/NIC/IP group in the deployment, for example, `cfy executions start scale -d vms -p scalable_entity_name=scalable_compute -p delta=3
3. Get the IPs of all of the VMs.
4. Edit the scaleuplistparams.yaml file with the new IPs.
5. Install the scale up list example: `cfy install cloudify-ansible-plugin/examples/scale-list-example-blueprint.yaml -b scaleuplist`
6. Install Scale Up list: `cfy executions start scaleuplist -d scaleuplist -p scaleuplistparams.yaml`
7. If you SSH into all of the machines and read `/tmp/testfile.txt` you should see that they received the params.


