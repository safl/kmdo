DOC_BUILD_DIR=build
PROJECT_NAME=kmdo
PROJECT_VERSION_MAJOR=$(shell grep "VERSION_MAJOR = ." src/kmdo/__init__.py | cut -d " " -f 3)
PROJECT_VERSION_MINOR=$(shell grep "VERSION_MINOR = ." src/kmdo/__init__.py | cut -d " " -f 3)
PROJECT_VERSION_PATCH=$(shell grep "VERSION_PATCH = ." src/kmdo/__init__.py | cut -d " " -f 3)
PROJECT_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}
NEXT_VERSION_PATCH=$$((${PROJECT_VERSION_PATCH} + 1))
NEXT_VERSION=${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${NEXT_VERSION_PATCH}

INSTALL_OPTS?=

.PHONY: default
default: clean build
	@echo "# DONE!"

.PHONY: all
all: clean uninstall build install
	@echo "# DONE!"

.PHONY: uninstall
uninstall:
	pipx uninstall kmdo || true

.PHONY: install
install:
	pipx install dist/*.tar.gz

.PHONY: clean
clean:
	@rm -r dist || true

.PHONY: release-build
build:
	python3 setup.py sdist

.PHONY: release-upload
upload:
	twine upload dist/*

.PHONY: release
release: clean build upload
	@echo -n "# rel: "; date

.PHONY: bump
bump:
	@echo "# Bumping '${PROJECT_VERSION}' to '${NEXT_VERSION}'"
	@sed -i -e s/"version = \".*\""/"version = \"${NEXT_VERSION}\""/g docs/src/conf.py
	@sed -i -e s/"release = \".*\""/"release = \"${NEXT_VERSION}\""/g docs/src/conf.py
	@sed -i -e s/"^VERSION_PATCH = .*"/"VERSION_PATCH = ${NEXT_VERSION_PATCH}"/g src/kmdo/__init__.py
