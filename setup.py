from setuptools import setup


def readfile(filename):
    try:
        with open(filename) as f:
            return f.read()
    except FileNotFoundError:
        return ''


setup(
    name='cfly',
    version='0.9.9',
    description='Build python extensions on-the-fly. Run C++ code directly from Python',
    long_description=readfile('README.md'),
    url='https://github.com/pymet/cfly',
    packages=['cfly'],
    install_requires=['jinja2'],
    author='pymet',
    author_email='office@pymet.com',
    license='MIT',
    classifiers=[],
    keywords=['cfly', 'build', 'extension', 'c++'],
)
