from setuptools import setup, find_packages




install_requires = []
with open('requirements.txt') as reqs:
    for line in reqs.readlines():
        req = line.strip()
        if not req or req.startswith('#'):
            continue
        install_requires.append(req)




package_name = 'peeler_driver_pkg'

setup(
    name='peeler_driver_pkg',
    version='0.0.1',
    packages = find_packages(),
    # data_files=[
    #     ('share/ament_index/resource_index/packages',
    #         ['resource/' + package_name]),
    #     ('share/' + package_name, ['package.xml']),
    # ],
    install_requires = install_requires,
    zip_safe=True,
    # python_requires=">=3.8",
    maintainer='Sanjiv Parthasarathy and Rafael Vescovi',
    maintainer_email='sparthasarathy@anl.gov',
    description='Driver for the Brooks Peeler',
    url='https://github.com/AD-SDL/azenta_driver/tree/main/peeler_driver', 
    # license='MIT License',
    entry_points={ 
        'console_scripts': [
            #  'peeler_driver = peeler_driver_pkg.peeler_driver:main_null',
      

        ]
    },

    
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)