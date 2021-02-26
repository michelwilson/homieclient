from distutils.core import setup


setup(
    name='homieclient',
    version='0.1dev',
    packages=['homieclient',],
    license='MIT License',
    author='Michel Wilson',
    description='Client to interact with Homie IoT devices via MQTT',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.0',
    platforms='any',
    install_requires=open('requirements.txt').read().split('\n'),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Home Automation"
    ]
)
