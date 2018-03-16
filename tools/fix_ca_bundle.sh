# When the functional tests are run in a devstack environment, we
# need to make sure that the python-requests module installed by
# tox in the test environment can find the distro-specific CA store
# where the devstack certs have been installed.
#
# assumptions:
# - devstack is running
# - the devstack tls-proxy service is running
# - the environment var OS_TESTENV_NAME is set in tox.ini (defaults
#   to 'functional'
#
# This code based on a function in devstack lib/tls
function set_ca_bundle {
    local python_cmd=".tox/${OS_TESTENV_NAME:-functional}/bin/python"
    local capath=$($python_cmd -c $'try:\n from requests import certs\n print (certs.where())\nexcept ImportError: pass')
    # of course, each distro keeps the CA store in a different location
    local fedora_CA='/etc/pki/tls/certs/ca-bundle.crt'
    local ubuntu_CA='/etc/ssl/certs/ca-certificates.crt'
    local suse_CA='/etc/ssl/ca-bundle.pem'

    # the distro CA is rooted in /etc, so if ours isn't, we need to
    # change it
    if [[ ! $capath == "" && ! $capath =~ ^/etc/.* && ! -L $capath ]]; then
        if [[ -e $fedora_CA ]]; then
            rm -f $capath
            ln -s $fedora_CA $capath
        elif [[ -e $ubuntu_CA ]]; then
            rm -f $capath
            ln -s $ubuntu_CA $capath
        elif [[ -e $suse_CA ]]; then
            rm -f $capath
            ln -s $suse_CA $capath
        else
            echo "can't set CA bundle, expect tests to fail"
        fi
    fi
}

set_ca_bundle
