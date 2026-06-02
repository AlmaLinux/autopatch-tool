SPECFILE            = $(shell find -maxdepth 1 -type f -name *.spec)
SPECFILE_NAME       = $(shell awk '$$1 == "Name:"     { print $$2 }' $(SPECFILE) )
SPECFILE_VERSION    = $(shell awk '$$1 == "Version:"  { print $$2 }' $(SPECFILE) )
SPECFILE_RELEASE    = $(shell awk '$$1 == "Release:"  { print $$2 }' $(SPECFILE) )
TARFILE             = $(SPECFILE_NAME)-$(SPECFILE_VERSION).tar.gz
DIST               ?= $(shell rpm --eval %{dist})

# Agent components are deployed from source (Ansible/gunicorn), never packaged
# in the RPM, so they are excluded from the build tarball.
sources:
	tar -zcf $(TARFILE) --exclude-vcs \
		--exclude='src/agent_handler.py' \
		--exclude='src/agent_orchestrator.py' \
		--exclude='src/__pycache__/agent_*' \
		--transform 's,^,$(SPECFILE_NAME)-$(SPECFILE_VERSION)/,' ansible src tests LICENSE README.md conf_example.yaml *py

clean:
	rm -rf build/ $(TARFILE)

srpm: sources
	rpmbuild -bs --define 'dist $(DIST)' --define "_topdir $(PWD)/build" --define '_sourcedir $(PWD)' $(SPECFILE)

rpm: sources
	rpmbuild -bb --define 'dist $(DIST)' --define "_topdir $(PWD)/build" --define '_sourcedir $(PWD)' $(SPECFILE)

# Docker-based test run (ported from run_tests_docker.sh).
# Builds an AlmaLinux 9 image with all dependencies and runs the test suite
# inside it. Dockerfile.test is generated on the fly and is git-ignored.
IMAGE_NAME     ?= autopatch-test-almalinux9
CONTAINER_NAME ?= autopatch-test-container

.PHONY: test-docker

test-docker:
	@echo "Generating Dockerfile.test..."
	@printf '%s\n' \
		'FROM almalinux:9' \
		'RUN dnf update -y && dnf install -y python3 python3-pip python3-rpm python3-devel python3-protobuf git rpm-build gcc gcc-c++ make which && dnf clean all' \
		'WORKDIR /app' \
		'COPY . .' \
		'RUN mkdir -p /root/.cas' \
		'COPY .cas/credentials /root/.cas/credentials' \
		'RUN pip3 install --no-cache-dir -r requirements.txt' \
		'RUN pip3 uninstall google-api-core google-api -y' \
		'RUN git config --global user.email "eabdullin@almalinux.org"' \
		'RUN git config --global user.name "eabdullin"' \
		'ENV PYTHONUNBUFFERED=1' \
		'ENV PYTHONPATH="./src:./"' \
		'CMD ["sh", "-c", "pytest tests"]' \
		> Dockerfile.test
	@echo "Building Docker image: $(IMAGE_NAME)"
	docker build -f Dockerfile.test -t $(IMAGE_NAME) .
	@docker rm -f $(CONTAINER_NAME) >/dev/null 2>&1 || true
	@echo "Running tests in Docker container..."
	@docker run --name $(CONTAINER_NAME) $(IMAGE_NAME); status=$$?; \
		if [ $$status -ne 0 ]; then \
			echo "Tests failed (exit $$status)"; \
			docker cp $(CONTAINER_NAME):/app/tests/results ./ 2>/dev/null || true; \
			rm -f Dockerfile.test; \
			exit $$status; \
		fi
	@rm -f Dockerfile.test
	@echo "Test run finished successfully!"
