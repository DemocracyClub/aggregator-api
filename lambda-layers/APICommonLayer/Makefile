build-APICommonLayer:
	cp -r $(ARTIFACTS_DIR)/../../../api/common/* .
	pip install --upgrade pip
	pip install --upgrade .[polars] --target "$(ARTIFACTS_DIR)/python/" --log /dev/null
	cp requirements.txt "$(ARTIFACTS_DIR)/python/installed-requirements.txt"
