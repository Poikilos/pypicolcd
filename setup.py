import setuptools

# For nose, see https://github.com/poikilos/mgep/blob/master/setup.py

long_description = ""
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = 'pypicolcd',
    version = '0.1',
    description = "The project includes a driverless module to access pixel-based picoLCD panels, and test programs.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
	'Topic :: System :: Hardware',
    ],
    keywords = 'python picoLCD Sideshow 256x64',
    url = "https://github.com/poikilos/pypicolcd",
    author = "Jake Gustafson",
    author_email = '7557867+poikilos@users.noreply.github.com',
    license = 'GPLv3+',
    # packages = setuptools.find_packages(),
    packages = ['pypicolcd'],
    # scripts = ['example'] ,
    # See https://stackoverflow.com/questions/27784271/how-can-i-use-setuptools-to-generate-a-console-scripts-entry-point-which-calls
    entry_points = {
	'console_scripts': ['pypicolcd-cli=pypicolcd.command_line:main'],
    },
    install_requires = [
	'pyusb',
	'Pillow'
    ]
 )
