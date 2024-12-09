from app.customer import insert_customer
from app.logs import insert_log

# Yeni müşteri ekleme
insert_customer("Frank", 1800)

# Yeni log kaydı ekleme
insert_log(1, None, "Info", "Müşteri sistemde oturum açtı.")
