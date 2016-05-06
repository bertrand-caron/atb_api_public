install-user:
	python setup.py install --user

install-sudo:
	python setup.py install

src3: src3/atb_api.py
.PHONY: src3

src3/atb_api.py: src2/atb_api.py
	cp $< $@
	2to3 -w $@
	sed -i "s/with open(fnme, 'w') as fh:/with open(fnme, 'wb') as fh:/g" src3/atb_api.py

