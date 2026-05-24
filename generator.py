import os 
import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd

fake = Faker('en_US')

# seed selection (to reproduce dataset)
Faker.seed(7)
random.seed(7)

# customer demographics
def profile_generator(num_customers=100):
    customers = []

    for _ in range(num_customers):
        tier = random.choices(
            ['Bronze', 'Silve', 'Gold', 'Platinum'],
            weights = [0.5, 0.3, 0.15, 0.05],
            k = 1
        )[0]

        profile = {
            "customer_id": f"CUST-{fake.unique.random_number(digits = 5, fix_len = True)}",
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "street_address": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "zipcode": fake.zipcode(),
            "birth_date": fake.date_of_birth(minimum_age = 18, maximum_age = 80).strftime('%Y-%m-%d'),
            "account_created": fake.date_between(start_date = '-3y', end_date = 'today').strftime('%Y-%m-%d'),
            "membership_tier": tier
        }

        customers.append(profile)
    
    return pd.DataFrame(customers)

# financial transaction 
def transaction_generator(df_customers, num_transactions = 500):
    transaction = []
    customer_ids = df_customers['customer_id'].tolist()

    categories = {
        'Electronics': (50.00, 1200.00),
        'Apparel': (15.00, 150.00),
        'Home & Kitchen': (20.00, 400.00),
        'Books': (10.00, 50.00),
        'Beauty': (10.00, 200.00)
    }

    for i in range(num_transactions):
        # rand customer and category 
        cust_id = random.choice(customer_ids)
        category = random.choice(list(categories.keys()))

        # price based on category range
        min_p, max_p = categories[category]
        amount = round(random.uniform(min_p, max_p), 2)

        # transaction failure
        status = random.choices(['Approved', 'Declined'], weights=[0.97, 0.03], k=1)[0]

        tx = {
            "transaction_id": f"TXN-{100000 + i}",
            "customer_id": cust_id,
            "timestamp": fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S'),
            "category": category,
            "amount_usd": amount,
            "payment_method": random.choice(['Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer']),
            "status": status
        }

        transaction.append(tx)

    return pd.DataFrame(transaction)

def main():
    print("Starting Synthetic Data Generator...")

    # data depth
    CUSTOMERS_COUNT = 250
    TRANSACTIONS_COUNT = 1000

    # generation of dataset 
    print(f"Generating {CUSTOMERS_COUNT} customer profiles...")
    df_customers = profile_generator(CUSTOMERS_COUNT)
    print(f"Generating {TRANSACTIONS_COUNT} transaction records...")
    df_transactions = transaction_generator(df_customers, TRANSACTIONS_COUNT)

    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)

    # save to CSV
    cust_file = os.path.join(output_dir, "customers.csv")
    tx_file = os.path.join(output_dir, "transactions.csv")
    df_customers.to_csv(cust_file, index=False)
    df_transactions.to_csv(tx_file, index=False)
    print("\nSuccess! Files saved to the 'output_data' folder:")
    print(f"   - {cust_file} ({len(df_customers)} rows)")
    print(f"   - {tx_file} ({len(df_transactions)} rows)")

    # preview
    print("\nCustomer Data Preview:")
    print(df_customers[['customer_id', 'name', 'membership_tier']].head(3))

if __name__ == "__main__":
    main()