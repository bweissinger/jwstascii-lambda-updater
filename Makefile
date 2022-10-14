ARTIFACTS_DIR ?= build

.PHONY: build
build:
	rm -rf dist || true
	python -m build -w

.PHONY: build_layer
build_layer: build
	rm -f $(ARTIFACTS_DIR)/jwstascii-lambda-updater.zip
	rm -rf $(ARTIFACTS_DIR)/python || true
	mkdir -p $(ARTIFACTS_DIR)/python
	python -m pip install -r requirements.txt -t $(ARTIFACTS_DIR)/python
	python -m pip install dist/*.whl -t $(ARTIFACTS_DIR)/python
	rm -rf $(ARTIFACTS_DIR)/python/PIL || true
	rm -rf $(ARTIFACTS_DIR)/python/Pillow* || true

.PHONY: package
package: build build_layer
	cp functions/lambda_function.py $(ARTIFACTS_DIR)/python
	cd $(ARTIFACTS_DIR)/python; zip -rq ../jwstascii-lambda-updater.zip *
