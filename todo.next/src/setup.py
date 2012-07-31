from distutils.core import setup
import py2exe

setup(name = "todo.next",
    version = "0.1",
    description = "A command line todo list organizer enhancing the todo.txt format",
    author = "Philipp Scholl",
    author_email = "pscholl+todonext@gmail.com",
    url = "https://github.com/philScholl/todo.next-proto",
    packages = [],
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