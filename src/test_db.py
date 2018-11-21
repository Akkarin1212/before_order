import db

mydb = None

def test_connection():
    global mydb
    mydb = db.connect_db()
    assert mydb

def test_get_dish_info():
    #info = db.get_dishes_info(mydb, "김밥")
    info = db.get_dish_info(mydb, "김밥")
    assert info
    assert info["name"]
    for key,value in info.items():
        print("Key: " + str(key) + " Value: " + str(value))


def test_get_available_dishes():
    #dish = db.get_available_dishes(mydb, "김밥")
    dish = db.get_available_dishes(mydb, ["김밥"])
    assert dish

# tests
test_connection()
test_get_dish_info()
test_get_available_dishes()