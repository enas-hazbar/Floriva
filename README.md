🌱 Floriva – Greenhouse Monitoring System

📖 Overview
Floriva is a smart greenhouse monitoring system that measures temperature, humidity, voltage, and light using an Arduino Rich Shield.
The data is sent to a Flask web app, stored in a MySQL database, and displayed live on a dashboard website.
When it gets dark, the system automatically turns on the lights, and when it’s bright, they turn off again.

⚙️ Features
-Real-time temperature, humidity, voltage, and light readings
-Automatic light control (dark/bright detection)
-Live dashboard using Flask and MySQL
-Login and admin system
-Dark and light dashboard modes

🧠 Hardware Setup (Arduino)
Components Used:
 -Arduino Uno R3
 -Rich Shield (with built-in sensors)
 -USB cable to connect Arduino to PC
 
Connections:
| Component              | Pin | Function                       |
| ---------------------- | --- | ------------------------------ |
| Temperature & Humidity | D12 | Reads temperature and humidity |
| Light Sensor           | A2  | Detects light intensity        |
| Voltage Sensor         | A3  | Reads voltage value            |

💻 Software Setup

1️⃣ Arduino Side

 Upload the Arduino sketch (`floriva.ino`) to your Arduino board using the Arduino IDE.
Required Libraries:
 -RichShield folder. 


Steps:
1. Open Arduino IDE
2. Go to Sketch → Include Library → Add Zip. library
3. Upload the RichShield Zip file
4. Upload your sketch
5. Open the Serial Monitor to confirm readings

2️⃣ Python (Flask) Side

 Install Required Packages:

In your terminal:
pip install flask
pip install flask-mysqldb
pip install pyserial
pip install python-dotenv
pip install bcrypt


  Run Flask App:

1. Make sure MySQL is running.
2. Create a database and add your connection info in the `.env` file:
  "DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=yourpassword
   DB_NAME=floriva_db "
   
"Database-name: Floriva
tables: there are 3 tables

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    telephone VARCHAR(20),
    greenhouse_name VARCHAR(100),
    greenhouse_num INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    device_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    date DATE NOT NULL,
    day_name VARCHAR(10),
    period ENUM('Morning', 'Afternoon', 'Evening') NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    voltage FLOAT,
    ldr INT,
    lights ENUM('ON',' OFF'),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
); "
3. Start the Flask app:
   python app.py
   
4. Open the app in your browser at:
   👉 `http://127.0.0.1:5000/`
📡 How It Works

1. Arduino reads the data (temperature, humidity, light, voltage).
2. Arduino sends data through serial communication to Flask.
3. Flask receives the data and saves it in the MySQL database.
4. The dashboard shows the live data in charts and tables.
5. The light sensor turns on/off LEDs automatically based on brightness.

🧪 Testing

- Verified that data transfers correctly between Arduino → Flask → MySQL.
- Tested light sensor: light ON when dark, OFF when bright.
- Confirmed website updates with live sensor readings.
- Checked login with valid and invalid credentials.

🧰 Tools Used

| Tool               | Purpose                         |
| ------------------ | ------------------------------- |
| Arduino IDE        | For coding and testing hardware |
| Visual Studio Code | For Flask web development       |
| MySQL Workbench    | To create and manage the database   
| Figma              | For dashboard design            |
| Lucid.app          | For ERD diagrams                |


Writing by Enas Hezabr

Would you like me to make this into a **downloadable `README.md` file** (so you can drop it directly into your project folder)?
