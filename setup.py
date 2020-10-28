import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mqtt-recorder",
    version="1.2.0",
    author="RPDSWTK",
    description="MQTT recorder tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rpdswtk/mqtt_recorder",
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': ['mqtt-recorder=mqtt_recorder.__main__:main'],
    },
    install_requires=[
        'paho-mqtt',
        'tqdm'
    ],
    python_requires='>=3.7',
)
