#### Variables ####

export ROOT_DIR ?= $(PWD)
export AMP_ROOT_DIR ?= $(ROOT_DIR)

export ANSIBLE_NAME ?= ansible-amp
export HOSTS_INI_FILE ?= $(AMP_ROOT_DIR)/hosts.ini

export EXTRA_VARS ?= "@$(AMP_ROOT_DIR)/vars/main.yml"

#### a. Debugging ####
amp-debug:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/debug.yml \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)

amp-pingall:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/pingall.yml \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)

#### b. Provision k8s with AMP ####
# AMP-install
amp-install: amp-monitor-install amp-monitor-load
amp-uninstall: amp-monitor-uninstall

#### c.2 Split (CU/DU) monitoring ####
AMP_SPLIT_LIMIT = $(if $(OCUDU_EFFECTIVE_NODES),$(OCUDU_EFFECTIVE_NODES),$(if $(OCUDU_NODE),$(OCUDU_NODE),ocudu_nodes))
AMP_SPLIT_ACTIVE_ARG = $(if $(OCUDU_EFFECTIVE_NODES),-e "ocudu_active_nodes=$(OCUDU_EFFECTIVE_NODES)",$(if $(OCUDU_NODE),-e "ocudu_active_nodes=$(OCUDU_NODE)",))

amp-split-start: ocudu-split-start amp-split-exporter-install amp-split-monitor-load
amp-split-stop: amp-split-monitor-uninstall amp-split-exporter-uninstall
amp-split-exporter-install:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/split.yml --tags install --limit $(AMP_SPLIT_LIMIT) \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)
amp-split-exporter-uninstall:
	@if [ -n "$(OCUDU_STOP_NODES)" ]; then \
		ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/split.yml --tags uninstall --limit $(OCUDU_STOP_NODES) \
			--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS); \
	else \
		echo "Skipping amp-split-exporter-uninstall: no running target OCUDU node containers"; \
	fi
amp-split-monitor-load:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/split.yml --tags install --limit master_nodes \
		$(AMP_SPLIT_ACTIVE_ARG) --extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)
amp-split-monitor-uninstall:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/split.yml --tags uninstall --limit master_nodes \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)
amp-split-monitor-cleanup:
	@if [ -z "$(OCUDU_DETECTED_NODES)" ]; then \
		ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/split.yml --tags uninstall --limit master_nodes \
			--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS); \
	else \
		echo "Preserving split monitoring in K8s (active OCUDU nodes: $(OCUDU_DETECTED_NODES))"; \
	fi

#### c. Provision Monitoring ####
amp-monitor-install:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/monitor.yml --tags install \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)
amp-monitor-uninstall:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/monitor.yml --tags uninstall \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)

#### c.1 Load Monitoring Dashboards ####
amp-monitor-load:
	ansible-playbook -i $(HOSTS_INI_FILE) $(AMP_ROOT_DIR)/monitor-load.yml --tags install \
		--extra-vars "ROOT_DIR=$(ROOT_DIR)" --extra-vars $(EXTRA_VARS)
