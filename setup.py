import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_requires(test=None):
    if test:
        req_file = "test-requirements.txt"
    else:
        req_file = "requirements.txt"

    with open(req_file, "r") as f:
        return [line.strip() for line in f]


setuptools.setup(
    name="badgrclient",
    packages=["badgrclient"],
    version="0.1",
    description="A python library for Badgr APIs",
    author="Snehal Baghel",
    author_email="snehalbaghel@gmail.com",
    url="https://github.com/snehalbaghel/badgrclient",
    keywords=["badgr", "openbadges", "api", "library"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
    license="GNU General Public License v3.0",
    install_requires=get_requires(),
    test_requires=get_requires(test=True),
)
