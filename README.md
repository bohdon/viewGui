To setup the dev environment, do the following in cmd (not git bash!):

	mayapy bootstrap.py
	bin\buildout

You'll need setuptools installed for this to work.

Once done, edit your source in `src/`, then when you need to test in maya, run:

	bin\python setup.py sdist
	
This will create a source dist (tar-ball/zip-ball) that you can easy_install.
The `setup.cfg` will append `dev-DATE` to the version, so each release will be 
"newer" than the last, ensuring a smooth upgrade process from easy_install.