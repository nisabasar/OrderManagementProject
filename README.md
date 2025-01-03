Order Management System

This project is a Flask-based web application designed for managing an order management system with functionalities for both admins and customers. It provides tools for managing products, customer orders, and stock, with user roles (admin and customer) to ensure controlled access.

Features

Admin Panel

Product Management:

Add new products.

Update stock.

Delete products.

Order Management:

Approve or reject customer orders.

View and process pending orders.

Customer Management:

View all registered customers.

Manage customer priority scores.

Critical Stock Monitoring:

Highlight products with stock below 10.

Activity Logs:

Maintain logs of all major actions (e.g., stock updates, order approvals).

Customer Panel

Product Browsing:

View available products with stock and pricing details.

Shopping Cart:

Add or remove products to/from the cart.

Checkout orders.

Order Tracking:

View status of past and pending orders.

Technology Stack

Backend: Flask (Python)

Database: MySQL

Frontend: HTML, CSS, JavaScript (Bootstrap 5)

Session Management: Flask sessions

Logging: Custom logging system integrated with the database

Requirements

Python 3.8+

MySQL

Required Python Libraries:

Flask

MySQLdb

Jinja2

Chart.js (for visualizing stock levels)

Installation and Setup

Step 1: Clone the Repository

git clone https://github.com/yourusername/order-management-system.git
cd order-management-system

Step 2: Install Python Dependencies

Use pip to install the required dependencies:

pip install -r requirements.txt

Step 3: Configure the Database

Create a MySQL database named OrderManagement.

Import the provided SQL schema file to set up the required tables:

mysql -u root -p OrderManagement < schema.sql

Update the get_database_connection function in app/database.py with your MySQL credentials.

Step 4: Run the Application

Start the Flask application by running the following command:

python main.py

The application will be available at http://127.0.0.1:5000.

Usage

Admin Credentials

Upon setting up the database, you can log in as an admin using the credentials defined in the Users table.

Endpoints

Admin-Specific Endpoints

/admin-panel: View and manage all admin functionalities.

/add-admin: Add new admin users.

/update-stock: Update product stock.

Customer-Specific Endpoints

/customer-panel: Access the customer dashboard.

/add-to-cart: Add a product to the shopping cart.

/checkout: Finalize an order.

General Endpoints

/login: User login.

/register: Customer registration.

Logs

Activity logs are accessible in the admin panel under the "Log Management" section. These logs provide insights into all major system actions, including errors and updates.

Screenshots

Admin Panel

Product Management Interface

Order Approval Dashboard

Customer List with Priority Scores

Customer Panel

Product Browsing and Shopping Cart

Order History

Development Notes

Concurrency Management: Customer orders are processed using threading to handle multiple simultaneous actions efficiently.

Priority System: Customer priority scores are calculated dynamically based on waiting time and customer type.

Security: Admin features are protected by session-based role validation.

License

This project is licensed under the MIT License. See the LICENSE file for details.
