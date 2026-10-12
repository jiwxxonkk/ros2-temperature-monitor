from setuptools import find_packages, setup

package_name = 'sensor_monitor_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/sensor_system.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jiwon',
    maintainer_email='jiwon@todo.todo',
    description='Temperature and humidity monitoring nodes',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        	'temperature_publisher = sensor_monitor_py.temperature_publisher:main',
        	'monitor_node = sensor_monitor_py.monitor_node:main',
        	'threshold_client = sensor_monitor_py.threshold_client:main',
	],
    },
)
