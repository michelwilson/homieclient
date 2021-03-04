from setuptools import setup


setup(
    name='homieclient',
    version='0.0.1',
    package_dir={'': 'src'},
    packages=['homieclient',],
    license='MIT License',
    author='Michel Wilson',
    author_email='michel@crondor.net',
    url='https://github.com/michelwilson/homieclient',
    description='Client to interact with Homie IoT devices via MQTT',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.0',
    platforms='any',
    install_requires=[
        'paho-mqtt==1.5.1'
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Home Automation"
    ]
)
