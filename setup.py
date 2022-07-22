from setuptools import setup, find_packages
setup(
    name='LESO',
    version='0.1.0',
    description='A minimal and low-code multi-mode framework to investigate cost-optimal renewable energy systems and help guide policy and decission makers in the energy transition.',
    url='https://github.com/thesethtruth/LESO',
    author='Seth van Wieringen',
    author_email='seth@uu-engineering.nl',
    license='MIT',

    classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers :: Energy consultants',
    'Topic :: Energy Transition :: Optimization :: ETM :: MILP :: Wind :: Solar',

    # Pick your license as you wish (should match "license" above)
    'License :: MIT License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3',
],
    packages=find_packages(include=["LESO", "LESO.*"]),  # include all packages under src
    package_data={
        # And include any *.pkl files found in the "data" subdirectory
        # of the "ETMeta" package, also:
        "LESO": ["data/*.pkl"],
        "LESO": ["data/*.csv"],
    },
    install_requires=[
        'pandas',
        'numpy',
        'pyomo',
        'pvlib',
        'windpowerlib',
        'ema-workbench',
        'xarray',
        'requests',
        'beautifulsoup4',
        'xarray',
        'openpyxl',
        'pyproj'
    ],
    python_requires='>=3.6',
)