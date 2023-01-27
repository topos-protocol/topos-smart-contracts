import brownie
from brownie.convert.datatypes import HexString

import const as c


def test_insert_reverts_on_key_already_exists(admin, bytes_32_sets_test):
    insert_test_key(admin, bytes_32_sets_test)
    with brownie.reverts("Bytes32Set: key already exists in the set."):
        # should revert when trying to insert the same key
        insert_test_key(admin, bytes_32_sets_test)


def test_insert_inputs_data(admin, bytes_32_sets_test):
    insert_test_key(admin, bytes_32_sets_test)
    assert key_exists(admin, bytes_32_sets_test) is True


def test_remove_reverts_on_key_does_not_exist(admin, bytes_32_sets_test):
    with brownie.reverts("Bytes32Set: key does not exist in the set."):
        remove_test_key(admin, bytes_32_sets_test)


def test_remove_deletes_data(admin, bytes_32_sets_test):
    insert_test_key(admin, bytes_32_sets_test)
    remove_test_key(admin, bytes_32_sets_test)
    assert key_exists(admin, bytes_32_sets_test) is False


def test_get_count(admin, bytes_32_sets_test):
    count = 1
    insert_test_key(admin, bytes_32_sets_test)
    assert get_count(admin, bytes_32_sets_test) == count


def test_key_at_index(admin, bytes_32_sets_test):
    index = 0
    insert_test_key(admin, bytes_32_sets_test)
    assert get_key_at_index(admin, bytes_32_sets_test, index) == HexString(
        c.TEST_KEY, "bytes32"
    )


# internal functions #
def insert_test_key(admin, bytes_32_sets_test):
    bytes_32_sets_test.insert(c.TEST_KEY, {"from": admin})


def remove_test_key(admin, bytes_32_sets_test):
    bytes_32_sets_test.remove(c.TEST_KEY, {"from": admin})


def get_count(admin, bytes_32_sets_test):
    return bytes_32_sets_test.count({"from": admin})


def key_exists(admin, bytes_32_sets_test):
    return bytes_32_sets_test.exists(c.TEST_KEY, {"from": admin})


def get_key_at_index(admin, bytes_32_sets_test, index):
    return bytes_32_sets_test.keyAtIndex(index, {"from": admin})
