#### Variables ####

export OCUDU_ROOT_DIR ?= $(PWD)

export HOSTS_INI_FILE ?= hosts.ini

export EXTRA_VARS ?= ""

#### a. Debugging ####
ocudu-pingall:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/pingall.yml \
		--extra-vars $(EXTRA_VARS)

#### b. Provision docker ####
ocudu-docker-install:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/docker.yml --tags install \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)

#### a2. Simulated nodes (node2/node3 as Docker-in-Docker containers on the master node) ####
# Restrict split/uesim/router/nodes targets to one node (e.g. OCUDU_NODE=node2) or
# auto-detect running node containers when a subset of [ocudu_nodes] is active.
OCUDU_INVENTORY_NODES := $(shell awk '/^\[ocudu_nodes\]/{f=1;next} /^\[/{f=0} f && /^[a-zA-Z0-9_-]+/{print $$1}' $(HOSTS_INI_FILE) 2>/dev/null)
OCUDU_RUNNING_CONTAINERS = $(shell docker ps --format '{{.Names}}' 2>/dev/null)
OCUDU_DETECTED_NODES = $(strip $(filter $(OCUDU_INVENTORY_NODES),$(OCUDU_RUNNING_CONTAINERS)))
OCUDU_REQUESTED_NODES = $(if $(OCUDU_NODE),$(shell echo "$(OCUDU_NODE)" | tr ',' ' '),$(OCUDU_INVENTORY_NODES))
OCUDU_STOP_DETECTED = $(strip $(filter $(OCUDU_REQUESTED_NODES),$(OCUDU_RUNNING_CONTAINERS)))
export OCUDU_EFFECTIVE_NODES = $(if $(OCUDU_NODE),$(OCUDU_NODE),$(if $(OCUDU_DETECTED_NODES),$(shell echo $(OCUDU_DETECTED_NODES) | tr ' ' ','),))
export OCUDU_STOP_NODES = $(if $(OCUDU_STOP_DETECTED),$(shell echo $(OCUDU_STOP_DETECTED) | tr ' ' ','),)
OCUDU_LIMIT_ARG = $(if $(OCUDU_EFFECTIVE_NODES),--limit $(OCUDU_EFFECTIVE_NODES),)
OCUDU_TARGET_NODES_ARG = $(if $(OCUDU_NODE),-e "ocudu_target_nodes=$(OCUDU_NODE)",)

ocudu-nodes-up:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/nodes.yml --tags up \
		$(OCUDU_TARGET_NODES_ARG) --extra-vars $(EXTRA_VARS)
ocudu-nodes-down:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/nodes.yml --tags down \
		$(OCUDU_TARGET_NODES_ARG) --extra-vars $(EXTRA_VARS)

ocudu-router-install:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/router.yml --tags install \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)
ocudu-router-uninstall:
	@if [ -n "$(OCUDU_STOP_NODES)" ]; then \
		ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/router.yml --tags uninstall \
			--limit $(OCUDU_STOP_NODES) --extra-vars $(EXTRA_VARS); \
	else \
		echo "Skipping ocudu-router-uninstall: no running target OCUDU node containers"; \
	fi

ocudu-dpdk-install:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/dpdk.yml --tags install \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)

ocudu-dpdk-status:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/dpdk-status.yml \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)

ocudu-dpdk-verify:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/dpdk-verify.yml \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)

ocudu-gnb-start:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/gNB.yml --tags start \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)
ocudu-gnb-stop:
	@if [ -n "$(OCUDU_STOP_NODES)" ]; then \
		ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/gNB.yml --tags stop \
			--limit $(OCUDU_STOP_NODES) --extra-vars $(EXTRA_VARS); \
	else \
		echo "Skipping ocudu-gnb-stop: no running target OCUDU node containers"; \
	fi

ocudu-split-start:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/gNBSplit.yml --tags start \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)
ocudu-split-stop:
	@if [ -n "$(OCUDU_STOP_NODES)" ]; then \
		ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/gNBSplit.yml --tags stop \
			--limit $(OCUDU_STOP_NODES) --extra-vars $(EXTRA_VARS); \
	else \
		echo "Skipping ocudu-split-stop: no running target OCUDU node containers"; \
	fi

ocudu-uesim-start:
	ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/uEsimulator.yml --tags start \
		$(OCUDU_LIMIT_ARG) --extra-vars $(EXTRA_VARS)
ocudu-uesim-stop:
	@if [ -n "$(OCUDU_STOP_NODES)" ]; then \
		ansible-playbook -i $(HOSTS_INI_FILE) $(OCUDU_ROOT_DIR)/uEsimulator.yml --tags stop \
			--limit $(OCUDU_STOP_NODES) --extra-vars $(EXTRA_VARS); \
	else \
		echo "Skipping ocudu-uesim-stop: no running target OCUDU node containers"; \
	fi

ocudu-gnb-install: ocudu-docker-install ocudu-router-install ocudu-gnb-start
ocudu-gnb-uninstall: ocudu-gnb-stop ocudu-router-uninstall

ocudu-split-install: ocudu-nodes-up ocudu-docker-install ocudu-router-install ocudu-split-start ocudu-uesim-start
ocudu-split-uninstall: ocudu-uesim-stop ocudu-split-stop ocudu-router-uninstall ocudu-nodes-down
