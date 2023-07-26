# Aether-On-Ramp
This repository builds a standalone Aether core with a physical RAN setup, including AMF and gNbsimulation.

To download the Aether-On-Ramp repository, use the following command:
```
git clone --recursive https://gitlab.com/onf-internship/aetheronramp.git
```

After cloning the repository, start the Ansible Docker environment using `make ansible`.
This repository utilizes the following repositories as submodules.

---

## Aether 5G Core - 5GC

The 5gc repository builds a standalone Aether core with a physical RAN setup. It utilizes the k8 repository as a submodule to create a multi-node cluster and run the 5g-aether core on top.

### Step-by-Step Installation
To install the 5g-core, follow these steps:
1. Set the configuration variables in the vars/main.yaml file.
   - Set the "standalone" parameter to deploy the core independently from roc.
   - Specify the "data_iface" parameter as the network interface name of the machine.
   - Set the "values_file" parameter:
     - Use "hpa-5g-values.yaml" for a stateless 5g core.
     - Use "nohpa-5g-values.yaml" for a stateful 5g core.
   - The "ran_subnet" parameter if left empty, core will use the subnet of "data_iface" for UPF.
2. Add the hosts to the init file.
3. Run `make ansible`.
4. In the running Ansible docker terminal, run `make 5gc-install`.
   - It creates networking interfaces for UPF, such as access/core, using `5gc-router-install`.
   - Finally, it installs the 5g core using the values specified in `5gc-core-install`.
     - The installation process may take up to 3 minutes.

#### One-Step Installation
To install 5gc in one go, run `make 5gc-install`.
#### Uninstall
   - run `make 5gc-install`

<br />

---

## AMP - Aether Management Platform

The AMP repository is responsible for building the Aether Management Platform, which includes Aether-ROC and a monitoring system.

To install AMP, follow these step-by-step instructions:

2. Install ROC:
   - Specify the Helm charts for `atomix`, `onosproject`, and `aether_roc`.
   - Run the `roc-install` command.
   - For 5G, use the `make 5g-roc-install` command. For 4G, use the `make 4g-roc-install` command.

3. Install Monitoring:
   - Specify the Helm charts for `monitor` and `monitor-crd`.
   - Run the `monitor-install` command.

#### One-Step Installation
To install AMF in one go, run `amp-install`.
#### Uninstall
   - run `make monitor-uninstall; make roc-uninstall`


<br />

---

## gNbsim

The gnbsim repository enables the building of a multi-container and multi-node cluster of gNbsim using Docker. This allows you to run gNbsim simulations on multiple VMs, with the flexibility to run multiple containers on each VM.

### Step-by-Step Installation
To install gnbsim, follow these steps:

1. Install Docker by running `make gnbsim-docker-install`.
2. Configure the network for gnbsim:
   - Set the "data_iface" parameter to the network interface name of the machine.
   - Set "mcavlan_iface" to the name of the macvlan interface to be created.
   - Set "macvlan_network_name" to the name of the Docker network to be created.
   - Set "subnet_prefix" to the first two bytes of the subnet, which should correspond to the "custome_ran_subnet" of 5g-core or the machine's subnet.
3. Start the gNbsim Docker containers using `make gnbsim-docker-start`:
   - Set the container "image" for gNbsim.
   - Set "prefix" to the desired name for the gNbsim containers.
   - Set "count" to the number of containers to be instantiated on each VM.
4. Start the simulation:
   - Set "amf.ip" to the IP address of the core machine.
   - Set "ueid_base" to the starting IMSI number.
     - Each container will have a different starting IMSI number.
   - Set "ue_per_pod" to the number of UEs on each gNbsim container.
   - Set the "gnbsims" array with a list of key-value pairs:
     - Each key represents the container number (numeric).
     - The corresponding value `config_file` is the config template file for gNbsim.
   - Run `make gnbsim-simulator-start`.
5. Check the results:
   - Enter one of the Docker containers using `docker exec -it *prefix*-1 bash`.
   - Use `cat summary.log` to view the last result.
   - To check the logs generated by gnbsim, use `cat *gnbsim*.log`.

### One-Step Installation
To install gnbsim in one go, run `make gnbsim-simulator-setup-install`.

### Uninstall
To uninstall gnbsim, run `make gnbsim-simulator-setup-uninstall`.    


<br />

---
## K8 Cluster

The K8 Cluster repository is responsible for building a multi-node K8 cluster using rke2 and installing Helm. To set up the K8 cluster, you need to provide the following configurations:

1. Node configurations with IP addresses in the `host.ini` file.
   - You can specify both master and worker nodes in this file.

2. rke2 configuration parameters in the `./var/main.yaml` file.
   - Here, you can define the rke2 version and other relevant configurations.

3. Rke2 cluster parameters file in the `config` folder.
   - This file contains the necessary parameters for the cluster setup.

To install the K8 cluster, run the command `make k8s-install`. Once the installation is complete, you can check the status of the cluster by executing the following command on the master node:

```
sudo /var/lib/rancher/rke2/bin/kubectl get nodes --kubeconfig /etc/rancher/rke2/rke2.yaml
```

Here are some useful commands for managing the K8 cluster:
```
1. kubectl get nodes - Displays the list of nodes in the cluster.
2. sudo /var/lib/rancher/rke2/bin/kubectl get nodes --kubeconfig /etc/rancher/rke2/rke2.yaml - Retrieves the nodes using the specified kubeconfig file.
```

To uninstall the K8 cluster, you can use the command `make k8s-uninstall`. This will destroy the cluster and remove all associated resources.

<br />

---
---

# TODOs
1. Explain host.ini structure
2. Check node connectivity (ping)
2. Add a node to cluster
3. Remove Node from cluster
4. Add more gNbsim container

<!-- 
### To make multiNode setup to single Node
1. Destroy cluster using `make aether-uninstall`
2. update host.ini file 
3. Deploy cluster using `5gc-install` 
4. Setup gNbSim
    a. Check amf ip address is set to core ip adddes
    b. Set SameMachineAsCore=true
    c. Set "subnet_prefix" to the first two bytes of the subnet, which should correspond to the "custome_ran_subnet" of 5g-core or the machine's subnet.
    d. Run `gnbsim-simulator-setup-install`

### To setup Gnbsim on same machine as Core
 set SameMachineAsCore = true
 make sure gnbsim.subnet_prefix has same prefix value core.custome_ran_subnet
>

