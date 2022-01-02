from setuptools import setup
from os import listdir, system as syscall
from os.path import join as ojoin
from sys import argv as sargs, stderr

package_name = "sh_gui"

def prefixed_files_in(target_dir):
    return [ojoin(target_dir, f) for f in listdir(target_dir)]

if "--dry-run" in sargs:
    for filename_ui in listdir("ui"):
        file_ui = ojoin("ui", filename_ui)
        file_py = ojoin("scripts", "Ui_{0}.py".format(filename_ui.replace(".ui", "")))
        rc = syscall("pyuic5 -o \"{0}\" \"{1}\" >/dev/null".format(file_py, file_ui))
        assert (0 == rc), "Failed to build '{0}' to '{1}': {2}".format(file_ui, file_py, rc)

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", [
            "config/params.yaml",
        ]),
        ("share/" + package_name + "/launch", prefixed_files_in("launch")),
        ("lib/" + package_name + "/scripts", prefixed_files_in("scripts")),
        ("share/" + package_name + "/images", [
            "images/kyoto.png",
        ]),
        ("share/" + package_name + "/images/traffic_lights", prefixed_files_in("images/traffic_lights")),
        ("share/" + package_name + "/style", prefixed_files_in("style")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    author="R. Nick Vandemark",
    author_email="rnvandemark@gmail.com",
    maintainer="R. Nick Vandemark",
    maintainer_email="rnvandemark@gmail.com",
    keywords=["ROS2"],
    classifiers=[
        "Intended Audience :: Me",
        "License :: BSD",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
    description="The GUI to interact with the smart home.",
    license="BSD",
    entry_points={
        "console_scripts": [
            "sh_gui = sh_gui.sh_gui:main",
        ]
    }
)
