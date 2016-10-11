PYTHON_BIN_DIR = /usr/local/python35/bin

install-user:
	python setup.py install --user

install-sudo:
	python setup.py install

src2: src2/atb_api.py
.PHONY: src2

src2/atb_api.py: src3/atb_api.py
	cp $< $@
	$(PYTHON_BIN_DIR)/3to2 -n -w $@
	sed -i "s/from io import open//g" $@
.PHONY: src2/atb_api.py
