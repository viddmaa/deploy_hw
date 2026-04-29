import requests

BASE_URL = "http://127.0.0.1:8000"


def test_idor():
    response = requests.get(
        f"{BASE_URL}/files/2",
        headers={"X-User": "alice"}
    )
    print(f"Test 1 status: {response.status_code}")
    print(f"Test 1 body: {response.text}")
    assert response.status_code == 404
    print("Test 1 passed: alice cannot access bob's file\n")


def test_owner_access():
    response = requests.get(
        f"{BASE_URL}/files/1",
        headers={"X-User": "alice"}
    )
    print(f"Test 2 status: {response.status_code}")
    print(f"Test 2 body: {response.text}")
    assert response.status_code == 200
    print("Test 2 passed: alice can access her own file\n")


def test_admin_delete():
    response = requests.delete(
        f"{BASE_URL}/files/2",
        headers={"X-User": "admin"}
    )
    print(f"Test 3 delete status: {response.status_code}")
    print(f"Test 3 delete body: {response.text}")
    assert response.status_code == 200

    check_response = requests.get(
        f"{BASE_URL}/files/2",
        headers={"X-User": "admin"}
    )
    print(f"Test 3 check status: {check_response.status_code}")
    print(f"Test 3 check body: {check_response.text}")
    assert check_response.status_code == 404
    print("Test 3 passed: admin deleted bob's file\n")


if __name__ == "__main__":
    test_idor()
    test_owner_access()
    test_admin_delete()
    print("All tests passed")