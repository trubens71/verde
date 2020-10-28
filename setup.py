from setuptools import setup

setup(
    name='verde',
    scripts=['scripts/verde.py','scripts/create_vis.py', 'scripts/inspect_multi_models.py', 'zsh/lp_clingo_vl.zsh'],
    packages=['src'],
    version='0.2',
    url='https://github.com/trubens71/verde',
    license='',
    author='trubens71',
    author_email='toby_rubenstein@letterboxes.org',
    description='Visualisation Recommender with Domain Extensions using Draco'
)