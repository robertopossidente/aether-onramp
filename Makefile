#### Variables ####

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
export ROOT_DIR := $(or $(ROOT_DIR),$(MAKEFILE_DIR:/=))
export AETHER_ROOT_DIR := $(or $(AETHER_ROOT_DIR),$(ROOT_DIR))

export SDRAN_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/sdran
export 5GC_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/5gc
export 4GC_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/4gc
export AMP_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/amp
export GNBSIM_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/gnbsim
export OAI_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/oai
export OSCRIC_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/oscric
export SRSRAN_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/srsran
export OCUDU_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/ocudu
export UERANSIM_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/ueransim
export N3IWF_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/n3iwf
export K8S_ROOT_DIR ?= $(AETHER_ROOT_DIR)/deps/k8s

export ANSIBLE_NAME ?= ansible-aether
export ANSIBLE_CONFIG ?= $(AETHER_ROOT_DIR)/ansible.cfg
export HOSTS_INI_FILE ?= $(AETHER_ROOT_DIR)/hosts.ini

export EXTRA_VARS ?= "@$(AETHER_ROOT_DIR)/vars/main.yml"

export KUBECTL ?= kubectl
export KUBE_NAMESPACE ?= aether-5gc
export WEBUI_SERVICE ?= webui

export DOCKER ?= docker
export WEBUI_GUI_DIR ?= $(AETHER_ROOT_DIR)/webui-gui
export WEBUI_GUI_IMAGE ?= aether-webui-gui
export WEBUI_GUI_CONTAINER ?= aether-webui-gui
export WEBUI_GUI_PORT ?= 8088
export WEBUI_GUI_UPSTREAM ?= http://172.30.255.119:30500
export WEBUI_GUI_USER ?=
export WEBUI_GUI_PASSWORD ?=
export WEBUI_GUI_READ_ONLY ?= false


#### Validate Ansible Configuration ####
aether-pingall:
	echo $(AETHER_ROOT_DIR)
	ansible-playbook -i $(HOSTS_INI_FILE) $(AETHER_ROOT_DIR)/pingall.yml \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)

#### Provision AETHER Components for 5G ####
aether-k8s-install: k8s-install
aether-k8s-uninstall: k8s-uninstall
aether-5gc-install: 5gc-install
aether-5gc-uninstall: 5gc-uninstall
aether-gnbsim-install: gnbsim-install
aether-gnbsim-uninstall: gnbsim-uninstall
aether-amp-install: amp-install
aether-amp-uninstall: amp-uninstall
aether-amp-split-start: amp-split-start
aether-amp-split-stop: amp-split-stop
aether-sdran-install: sdran-install
aether-sdran-uninstall: sdran-uninstall
aether-ueransim-install: ueransim-install
aether-ueransim-uninstall: ueransim-uninstall
aether-oai-gnb-install: oai-gnb-install
aether-oai-gnb-uninstall: oai-gnb-uninstall
aether-oai-uesim-start: oai-uesim-start
aether-oai-uesim-stop: oai-uesim-stop
aether-srsran-gnb-install: srsran-gnb-install
aether-srsran-gnb-uninstall: srsran-gnb-uninstall
aether-srsran-uesim-start: srsran-uesim-start
aether-srsran-uesim-stop: srsran-uesim-stop
aether-ocudu-gnb-install: ocudu-gnb-install
aether-ocudu-gnb-uninstall: ocudu-gnb-uninstall
aether-ocudu-nodes-up: ocudu-nodes-up
aether-ocudu-nodes-down: ocudu-nodes-down
aether-ocudu-hosts-install: ocudu-docker-install
aether-ocudu-split-start: ocudu-split-start
aether-ocudu-split-stop: ocudu-split-stop
aether-ocudu-uesim-start: ocudu-uesim-start
aether-ocudu-uesim-stop: ocudu-uesim-stop
aether-ocudu-split-install: ocudu-split-install amp-split-exporter-install amp-split-monitor-load
aether-ocudu-split-uninstall: amp-split-exporter-uninstall ocudu-split-uninstall amp-split-monitor-cleanup
aether-oscric-ric-install: oscric-ric-install
aether-oscric-ric-uninstall: oscric-ric-uninstall
aether-n3iwf-install: n3iwf-install
aether-n3iwf-uninstall: n3iwf-uninstall

#### Shortcut for QuickStart Only ####
aether-install: k8s-install 5gc-install gnbsim-install amp-install
aether-uninstall: amp-uninstall gnbsim-uninstall 5gc-uninstall k8s-uninstall

#### Shortcut for OCUDU Split Multi-Node (supports OCUDU_NODE=node2, node3, or both) ####
aether-ocudu-split-multi-install: k8s-install 5gc-install aether-webui-gui-start amp-install aether-ocudu-split-install
aether-ocudu-split-multi-uninstall: aether-ocudu-split-uninstall amp-uninstall aether-webui-gui-stop 5gc-uninstall k8s-uninstall

#### Provision AETHER for 4G ####
#### 4G/5G share router role ####
aether-4gc-install: 4gc-core-install 5gc-router-install
aether-4gc-uninstall: 4gc-core-uninstall 5gc-router-uninstall

#### Other Useful Targets ####
aether-5gc-reset: 5gc-core-reset
aether-4gc-reset: 4gc-core-uninstall 4gc-core-install
aether-gnbsim-run: gnbsim-simulator-run
aether-add-upfs: 5gc-upf-install
aether-remove-upfs: 5gc-upf-uninstall
aether-ueransim-run: ueransim-run
aether-ueransim-stop: ueransim-stop

#### Access WebUI locally without exposing the Service ####
webui-port-forward:
	$(KUBECTL) -n $(KUBE_NAMESPACE) port-forward svc/$(WEBUI_SERVICE) 5000:5000 5001:5001 8080:8080

#### WebUI GUI (Swagger em /docs) ####
.PHONY: aether-webui-gui-start aether-webui-gui-stop aether-webui-gui-logs
aether-webui-gui-start:
	$(DOCKER) build -t $(WEBUI_GUI_IMAGE) $(WEBUI_GUI_DIR)
	-$(DOCKER) rm -f $(WEBUI_GUI_CONTAINER)
	$(DOCKER) run -d --name $(WEBUI_GUI_CONTAINER) --restart unless-stopped \
		-p $(WEBUI_GUI_PORT):8088 \
		-e WEBUI_URL=$(WEBUI_GUI_UPSTREAM) \
		-e READ_ONLY=$(WEBUI_GUI_READ_ONLY) \
		-e GUI_USER='$(WEBUI_GUI_USER)' \
		-e GUI_PASSWORD='$(WEBUI_GUI_PASSWORD)' \
		$(WEBUI_GUI_IMAGE)
	@echo "WebUI GUI: http://<host>:$(WEBUI_GUI_PORT)/  Swagger: http://<host>:$(WEBUI_GUI_PORT)/docs"

aether-webui-gui-stop:
	-$(DOCKER) rm -f $(WEBUI_GUI_CONTAINER)

aether-webui-gui-logs:
	$(DOCKER) logs -f $(WEBUI_GUI_CONTAINER)

# Rules:
#	amp-install: amp-monitor-install amp-monitor-load
#	amp-uninstall: amp-monitor-uninstall

#	5gc-install: 5gc-router-install 5gc-core-install
#	5gc-uninstall: 5gc-core-uninstall 5gc-router-uninstall

## run gnbsim-docker-install before running setup
#	gnbsim-install: gnbsim-docker-router-install gnbsim-docker-start
#	gnbsim-uninstall:  gnbsim-docker-stop gnbsim-docker-router-uninstall


###  Provision k8s ####
#	k8s-install
#	k8s-uninstall

### Provision router ####
#	5gc-router-install
#	5gc-router-uninstall

### Provision core ####
#	5gc-core-install
#	5gc-core-uninstall
#	5gc-core-reset

### Provision  AMP ####
# amp-install: k8s-install amp-monitor-install amp-monitor-load
# amp-uninstall: amp-monitor-uninstall k8s-uninstall

### Provision and load Monitoring ###
# amp-monitor-install
# amp-monitor-load
# amp-monitor-uninstall

### Provision and run gnbsim ###
# 	gnbsim-docker-install
# 	gnbsim-docker-uninstall

# 	gnbsim-docker-router-install
# 	gnbsim-docker-router-uninstall

# 	gnbsim-docker-start
# 	gnbsim-docker-stop

# 	gnbsim-simulator-start

### Provision and run ueransim     ###
# 	ueransim-install
# 	ueransim-run
# 	ueransim-uninstall


#include at the end so rules are not overwritten
include $(K8S_ROOT_DIR)/Makefile
include $(GNBSIM_ROOT_DIR)/Makefile
include $(OAI_ROOT_DIR)/Makefile
include $(SRSRAN_ROOT_DIR)/Makefile
include $(OCUDU_ROOT_DIR)/Makefile
include $(5GC_ROOT_DIR)/Makefile
include $(4GC_ROOT_DIR)/Makefile
include $(AMP_ROOT_DIR)/Makefile
include $(SDRAN_ROOT_DIR)/Makefile
include $(UERANSIM_ROOT_DIR)/Makefile
include $(OSCRIC_ROOT_DIR)/Makefile
include $(N3IWF_ROOT_DIR)/Makefile
