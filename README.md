# README #


### What is this repository for? ###

* This module adds reporting functionality to define report lines per Tax Codes and report inclusive and exclusive tax amounts per tax code
  to help with generation of Australian GST reporting requirements for Odoo Customers.
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

* This module requires the isoweek python module to work (sudo pip install isoweek)
* Configuration
  You should comment out the tax code xml file from this module, if they are already present in the system
  Similarly to Financial Reports configuration, if there is a set of custom Tax Codes, you will need to appropriately define the Tax Report lines in the module
  prior to install
* Dependencies
  - isoweek python module
* Database configuration
* How to run tests
* Deployment instructions
