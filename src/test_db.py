import db

mydb = None

def test_connection():
    global mydb
    mydb = db.connect_db()
    assert mydb

def test_get_dish_info():
    info = db.get_dishes(mydb, "김밥")
    assert info
    assert info[0]["name"]


def test_get_available_dishes():
    dish = db.get_dishes(mydb, ["김밥"])
    assert dish

# tests
test_connection()
test_get_dish_info()
test_get_available_dishes()