# OnRamp Variables

File `main.yml` specifies global variables used to configure how Aether is deployed.
By default, it is configured for the Quick Start deployment. The other files define
common configurations (also called blueprints), any one of which you can copy to
`main.yml`, and then edit to account for your local details. The current set of
blueprints include:

* `main-quickstart.yml`: Configures the RAN emulator (gNBsim) to run in the same
   server as the Core. Equivalent to `main.yml` by default. Details documented
   [here](https://docs.aetherproject.org/onramp/start.html).

* `main-gnbsim.yml`: Configures the RAN emulator (gNBsim) to run in one or more
   servers, independent of the Core. Details documented
   [here](https://docs.aetherproject.org/onramp/gnbsim.html).

* `main-gNB.yml`: Configures the Core to work with an external 5G radio (gNB), with
   the Core running independent of AMP. Details documented
   [here](https://docs.aetherproject.org/onramp/gnb.html).

* `main-eNB.yml`: Configures the Core to work with an external 4G radio (eNB), with
   the Core running independent of AMP. Details documented
   [here](https://docs.aetherproject.org/onramp/gnb.html#support-for-enbs).

* `main-upf.yml`: Configures the Core with two UPFs and programs AMP
   with two slices, each associated with a distinct UPF. Details documented
   [here](https://docs.aetherproject.org/onramp/blueprints.html#multiple-upfs).

* `main-sdran.yml`: Configures the Core and SD-RAN in tandem, with
  RANSIM (running in the same Kubernetes namespace as SD-RAN)
  emulating various RAN elements. Details documented
  [here](https://docs.aetherproject.org/onramp/blueprints.html#sd-ran).

* `main-ueransim.yml`: Configures UERANSIM in place of gNBsim,
  providing a second way to direct workload at the Core. Details documented
  [here](https://docs.aetherproject.org/onramp/blueprints.html#ueransim).

* `main-sriov.yml`: Configures UPF in DPDK/SRIOV mode. It will help to improve
  UPF packet processing performance. Details documented
  [here](https://docs.aetherproject.org/onramp/blueprints.html#enable-sr-iov-and-dpdk).

* `main-oai.yml`: Configures the Core with an OAI-based 5G RAN,
  supporting another gNB option. Boolean variable `simulation` selects
  emulated or physical UE. Details documented
  [here](https://docs.aetherproject.org/onramp/blueprints.html#oai-5g-ran).

* `main-srsran.yml`: Configures the SD-Core with a srsRAN-based 5G RAN,
  supporting another gNB option. Boolean variable `simulation` selects
  emulated or physical UE. Details documented
  [here](https://docs.aetherproject.org/onramp/blueprints.html#srsran-5g).

* `main-ocudu.yml`: Configures the SD-Core with an OCUDU-based 5G RAN,
  supporting another gNB option. Boolean variable `simulation` selects
  emulated or simulated UE workload via the bundled srsRAN UE container.
  [here](https://docs.aetherproject.org/onramp/blueprints.html#ocudu).

* `main-ocudu-split.yml`: Same as `main-ocudu.yml` but the gNB is split into
  O-CU and O-DU containers connected over F1 (ZMQ radio, simulated UE). It is
  mutually exclusive with the monolithic gNB: stop one before starting the
  other. Use `cp vars/main-ocudu-split.yml vars/main.yml` or pass
  `EXTRA_VARS='"@vars/main-ocudu-split.yml"'`.

* `main-ocudu-split-multi.yml`: Configures multiple split OCUDU gNBs (one
  O-CU + O-DU + simulated UE stack per node in `[ocudu_nodes]`) sharing a
  single UPF and slice.

* `main-ocudu-split-multi-mocn.yml`: Same multi-node split OCUDU RAN topology
  as `main-ocudu-split-multi.yml`, configured for MOCN / Neutral Host
  multi-UPF routing where each subscriber group (IMSI) is dynamically anchored
  to a distinct network slice and dedicated UPF (`default_upf` in `aether-5gc`
  and `additional_upfs["1"]` in `aether-upf-1`).

* `main-n3iwf.yml`: Configures the SD-Core with a N3IWF entity for non-3GPP access.
  Details documented
  [here](https://docs.aetherproject.org/onramp/blueprints.html#non-3gpp-interworking-function).

## Proxy Configuration

All blueprint files include an optional `proxy` section for deploying Aether
behind an HTTP proxy. Set `proxy.enabled` to `true` and fill in the proxy URLs
to activate it. When disabled (the default), proxy settings have no effect on the
deployment. See the top-level `README.md` for details.
