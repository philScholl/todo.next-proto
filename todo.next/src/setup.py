from distutils.core import setup
import py2exe, codecs, os

# get description from README.rst
with codecs.open(os.path.join("..", "README.rst"), "r", "utf-8") as fp:
    long_description = fp.read()
    
setup(name = "todo.next",
    version = "0.4.7",
    description = "A command line todo list organizer based on the todo.txt format",
    long_description = long_description,
    author = "Philipp Scholl",
    author_email = "pscholl+todonext@gmail.com",
    url = "https://github.com/philScholl/todo.next-proto",
    packages = ["actions", "misc", "todo"],
    data_files = {"": "*.template"},
    requires = ["dateutil(<2.0)", "colorama"],
    scripts = ["todo.py",],
    console = ["todo.py",],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        # TODO: check this
        "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
        "Natural Language :: English",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities"
        ],
    )