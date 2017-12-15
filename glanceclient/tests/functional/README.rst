======================================
python-glanceclient functional testing
======================================

Idea
----

Run real client/server requests in the gate to catch issues which
are difficult to catch with a purely unit test approach.

Many projects (nova, keystone...) already have this form of testing in
the gate.


Testing Theory
--------------

Since python-glanceclient has two uses, CLI and python API, we should
have two sets of functional tests. CLI and python API. The python API
tests should never use the CLI. But the CLI tests can use the python API
where adding native support to the CLI for the required functionality
would involve a non trivial amount of work.


Functional Test Guidelines
--------------------------

The functional tests require:

1) A working Glance/Keystone installation (for example, devstack)
2) A yaml file containing valid credentials

If you are using devstack, a yaml file will have been created for you
with the name /etc/openstack/clouds.yaml.  The test code knows where
to find it, so if you're using devstack, you don't need to do anything
else.

If you are not using devstack you should create a yaml file
with the following format:

 clouds:
   devstack-admin:
     auth:
       auth_url: http://10.0.0.1:35357/v2.0
       password: example
       project_domain_id: default
       project_name: admin
       user_domain_id: default
       username: admin
     identity_api_version: '2.0'
     region_name: RegionOne

The tests will look for a file named 'clouds.yaml' in the
following locations (in this order, first found wins):

* current directory
* ~/.config/openstack
* /etc/openstack

You may also set the environment variable OS_CLIENT_CONFIG_FILE
to the absolute pathname of a file and that location will be
inserted at the front of the search list.
