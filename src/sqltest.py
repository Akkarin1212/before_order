import mysql.connector

mydb = mysql.connector.connect(
  host="beforeordermysqlserver.mysql.database.azure.com",
  user="goalkeeper@beforeordermysqlserver",
  password="Christian0118!",
  database="test",
  ssl_ca="BaltimoreCyberTrustRoot.crt.pem"
)

print(mydb)