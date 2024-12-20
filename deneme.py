from app.customer import insert_random_customers

if __name__ == "__main__":
    try:
        insert_random_customers()
        print("Rastgele müşteriler başarıyla oluşturuldu!")
    except Exception as e:
        print(f"Hata: {e}")
