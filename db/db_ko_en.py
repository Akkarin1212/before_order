import mysql.connector

def connect_db():
    mydb = mysql.connector.connect(
    host="beforeordermysqlserver.mysql.database.azure.com",
    user="goalkeeper@beforeordermysqlserver",
    password="Christian0118!",
    database="food",
    ssl_ca="ssl_certificiate.pem"
    )
    mydb.set_charset_collation('utf8mb4', 'utf8mb4_unicode_ci')
    return mydb

