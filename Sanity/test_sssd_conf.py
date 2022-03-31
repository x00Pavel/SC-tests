# author: Pavel Yadlouski <pyadlous@redhat.com>
from fixtures import *
from SCAutolib.exceptions import PatternNotFound
from SCAutolib.utils import (edit_config_, backup_)
from SCAutolib import logger
import pytest


@pytest.mark.skip
@pytest.mark.parametrize("file_path,target,restore,restart",
                         [("/etc/sssd/sssd.conf",
                          {"section": "pam",
                            "key": "p11_uri",
                            "val": "pkcs11:slot-description=Virtual%20PCD%2000%2000"},
                           True, ["sssd"])])
def test_su_login_p11_uri_slot_description(user, edit_config):
    """Test login with PIN to the system with p11_uri specified on specific
    slot in sssd.conf."""
    user.su_login_local_with_sc()


@pytest.mark.parametrize("file_path,target,restore,restart",
                         [("/etc/sssd/sssd.conf",
                           {"section": "pam",
                             "key": "p11_uri",
                             "val": "pkcs11:slot-description=Virtual%20PCD%2000%2001"},
                           True, ["sssd"])])
def test_su_login_p11_uri_wrong_slot_description(user, edit_config):
    """Test login with password to the system with wrong p11_uri with wrong
    slot description in sssd.conf."""
    user.su_login_local_with_passwd()


@pytest.mark.parametrize("file_path,target,restore,restart",
                         [("/etc/sssd/sssd.conf",
                          {"section": f"certmap/shadowutils/{local_user().USERNAME_LOCAL}",
                            "key": "matchrule",
                            "val": "<SUBJECT>.*CN=testuser.*"},
                           True, ["sssd"])])
def test_matchrule_defined_for_other_user(user, edit_config):
    """Test smart card login fail when sssd.conf do not contain
    [certmap/shadowutils/USER] section for the user from the SC. Instead,
    section for other ([certmap/shadowutils/WRONG_USER]) user is present"""
    # change section of sssd.conf to get [certmap/shadowutils/testuser]
    with open("/etc/sssd/sssd.conf", "r") as sources:
        sourcesdata = sources.read()
    sourcesdata = sourcesdata.replace(
        f'[certmap/shadowutils/{user.USERNAME_LOCAL}]',
        '[certmap/shadowutils/testuser]')
    with open("/etc/sssd/sssd.conf", "w") as sources:
        sources.write(sourcesdata)
    # print sssd.conf; restart service
    logger.warning("Custom changes were made in sssd.conf file:")
    logger.info(sourcesdata)
    restart_service("sssd")
    # run tests
    with pytest.raises(PatternNotFound):
        user.su_login_local_with_sc()
    user.su_login_local_with_passwd()


@pytest.mark.parametrize("file_path,target,restore,restart",
                         [("/etc/sssd/sssd.conf",
                           {"section": "pam",
                             "key": "p11_uri",
                             "val": "pkcs11:slot-description=Virtual%20PCD%2000%2000"},
                           True, ["sssd"])])
def test_su_login_p11_uri_user_mismatch(user, edit_config):
    """Test smart card login fail when sssd.conf do not contain user from
    the smart card (wrong user in matchrule)"""
    edit_config_("/etc/sssd/sssd.conf",
                 f"certmap/shadowutils/{user.USERNAME_LOCAL}",
                 "matchrule",
                 "<SUBJECT>.*CN=testuser.*")
    destination_path = backup_("/etc/sssd/sssd.conf")
    restart_service("sssd")
    with pytest.raises(PatternNotFound):
        user.su_login_local_with_sc()
    user.su_login_local_with_passwd()


@pytest.mark.parametrize("file_path,target,restore,restart",
                         [("/etc/sssd/sssd.conf",
                           {"section": f"certmap/shadowutils/{local_user().USERNAME_LOCAL}",
                             "key": "matchrule",
                             "val": "<SUBJECT>.*CN=testuser.*"},
                           True, ["sssd"])])
def test_user_mismatch(user, edit_config):
    """Test smart card login fail when sssd.conf do not contain user from
    the smart card (wrong user in matchrule)"""
    with pytest.raises(PatternNotFound):
        user.su_login_local_with_sc()
    user.su_login_local_with_passwd()


@pytest.mark.parametrize("file_path,target,restore,restart",
                         [("/etc/sssd/sssd.conf",
                           {"section": f"certmap/shadowutils/{local_user().USERNAME_LOCAL}",
                            "key": "matchrule",
                            "val": f"UID={local_user().USERNAME_LOCAL}"},
                           True, ["sssd"])])
def test_wrong_subject_in_matchrule(user, edit_config):
    """Test smart card login fail when sssd.conf contain wrong subject in
    the matchrule."""
    user.su_login_local_with_passwd()
