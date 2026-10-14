# AMP

## Aether Monitoring Platform

The amp repository builds the Aether Monitoring Platform. It relies on a k8s cluster that can be created from the k8s repository.

### Step-by-Step Installation
To install AMP, follow these steps:
1. Install a k8s cluster
   - Provision a Kubernetes cluster before installing AMP. Use the companion k8s repository or another supported cluster provisioning workflow.
2. Install Monitoring
   - Specify Helm chart settings for `monitor` and `monitor_crd`.
   - Run `make amp-monitor-install`.

#### One-Step Installation
To install AMP in one go, run `make amp-install`.
#### Uninstall
   - Run `make amp-uninstall`.

#### Split (CU/DU) monitoring
With AMP installed (`make aether-amp-install`) and a split gNB, run `make aether-amp-split-start`. It (re)starts the split gNB with metrics enabled, installs the `ocudu-exporter` systemd unit (port 9110) on the `ocudu_nodes` host, and loads the ServiceMonitor plus the "5G Split Dashboard (CU/DU)" Grafana dashboard (uid `aether-5g-split`). Remove with `make aether-amp-split-stop`.
