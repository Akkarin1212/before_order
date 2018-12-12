import mysql.connector
import csv

def connect_db():
    mydb = mysql.connector.connect(
    host="beforeordermysqlserver.mysql.database.azure.com",
    user="goalkeeper@beforeordermysqlserver",
    password="Christian0118!",
    database="food",
    ssl_ca="../src/ssl_certificiate.pem"
    )
    mydb.set_charset_collation('utf8mb4', 'utf8mb4_unicode_ci')
    return mydb

def insert_dishes(mydb, ko_dishes):
    # create sql cursor for querying statements, get result as dictionary
    cursor = mydb.cursor(buffered=True,dictionary=True)
    infos = []
    for ko_dish in ko_dishes:
        if ko_dish[1] and ko_dish[2]:
            query = ("INSERT INTO food.ko_en (name, dish_id)"
                    "VALUES ('{ko_name}', "
                    "(Select id from food.dish WHERE name = \"{en_name}\" )) "
                    "ON DUPLICATE KEY UPDATE id=id ".format(ko_name=ko_dish[2], en_name=ko_dish[1]))
            print(query)
            cursor.execute(query)
            print("Row: " + str(cursor.lastrowid))
            mydb.commit()
    cursor.close()
    return infos
    

with open('dish db_ko.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    #skip headers
    next(csv_reader, None)

    insert_dishes(connect_db(), csv_reader)
    # line_count = 0
    # for row in csv_reader:
    #     if line_count == 0:
    #         print(f'Column names are {", ".join(row)}')
    #         line_count += 1
    #     else:
    #         print(f'\t{row[0]} id, {row[1]} english\t, {row[2]} korean.')
    #         line_count += 1
    # print(f'Processed {line_count} lines.')
