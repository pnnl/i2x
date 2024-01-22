from setuptools import setup
import os

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
   name='transformer_thermal_models',
   version='1.0',
   description='Thermal modeling of hotspot temperatures for power transformers.',
   author='Zachary H Draper',
   author_email='zhdraper@deltaxresearch.com',
   packages=['transformer_thermal_models'],  #same as name
   install_requires=required, #external packages as dependencies
)
