PROJECT_NAME=kmdo

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

.PHONY: build
build:
	python3 -m build --sdist

.PHONY: upload
upload:
	twine upload dist/*

.PHONY: release
release: clean build upload
	@echo -n "# rel: "; date

.PHONY: test
test:
	python3 -m pytest

.PHONY: format
format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

.PHONY: lint
lint:
	ruff check src/ tests/

.PHONY: bump
bump:
	@current=$$(python3 -c "import kmdo; print(kmdo.__version__)"); \
	major=$$(echo "$$current" | cut -d. -f1); \
	minor=$$(echo "$$current" | cut -d. -f2); \
	patch=$$(echo "$$current" | cut -d. -f3); \
	patch=$$((patch + 1)); \
	new="$$major.$$minor.$$patch"; \
	sed -i "s/__version__ = \".*\"/__version__ = \"$$new\"/" src/kmdo/__init__.py; \
	echo "Bumped $$current -> $$new"
