BUILD_DIR?=build

default: doc doc-view-html

.PHONY: deps
deps:
	pip install -r requirements.txt --user

.PHONY: clean
clean:
	rm -fr $(BUILD_DIR) || true
	rm -f cscope.out || true

.PHONY: configure
configure: clean
	mkdir -p $(BUILD_DIR)

.PHONY: kmdo
kmdo:
	kmdo src/examples
	kmdo src

.PHONY: sphinx
sphinx:
	@mkdir -p $(BUILD_DIR)/html
	sphinx-build -b html -c src -E src $(BUILD_DIR)/html

# Produce the sphinx stuff
.PHONY: doc
doc: clean deps configure kmdo sphinx
	@echo "# DONE"

.PHONY: doc-view-html
doc-view-html:
	xdg-open $(BUILD_DIR)/html/index.html &
