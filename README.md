# 🌱 Floriva –  Greenhouse Monitoring System

## 📖 Overview

**Floriva** is a smart greenhouse monitoring system that measures **temperature**, **humidity**, **voltage**, and **light intensity** using an **Arduino Rich Shield**.
The data is sent to a **Flask web application**, stored in a **MySQL database**, and displayed live on a **dashboard website**.
When it gets dark, the system automatically turns on the lights — and turns them off again when it’s bright.

---

## ⚙️ Features

* 🌡️ Real-time temperature, humidity, voltage, and light readings
* 💡 Automatic light control (dark/bright detection)
* 📊 Live dashboard using Flask & MySQL
* 🔐 Login and admin system
* 🌓 Dark and light dashboard modes

---

## 🧠 Hardware Setup (Arduino)

### Components Used

* Arduino Uno R3
* Rich Shield (with built-in sensors)
* USB cable (to connect Arduino to PC)

### Connections

| Component              | Pin | Function                       |
| ---------------------- | --- | ------------------------------ |
| Temperature & Humidity | D12 | Reads temperature and humidity |
| Light Sensor           | A2  | Detects light intensity        |
| Voltage Sensor         | A3  | Reads voltage value            |

---

## 💻 Software Setup

### 1️⃣ Arduino Side

#### Steps

1. Open **Arduino IDE**
2. Go to `Sketch → Include Library → Add .ZIP Library`
3. Upload the **RichShield** ZIP file
4. Open the `floriva.ino` sketch
5. Upload it to your board
6. Open the **Serial Monitor** to confirm sensor readings

#### Required Libraries

* `RichShield`

---

### 2️⃣ Python (Flask) Side

#### Install Required Packages

Run the following in your terminal:

```bash
pip install flask flask-mysqldb pyserial python-dotenv bcrypt
```

#### Configure Environment Variables

Create a `.env` file and add your database credentials:

```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=floriva_db
```

---

### 🗄️ Database Setup

**Database Name:** `floriva_db`

Create the following tables in MySQL:

```sql
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
    lights ENUM('ON', 'OFF'),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);
```

---

### 🚀 Running the Flask App

1. Make sure **MySQL** is running
2. Start the Flask app:

   ```bash
   python app.py
   ```
3. Open your browser and go to:
   👉 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 📡 How It Works

1. Arduino reads data (temperature, humidity, light, voltage)
2. Data is sent via serial communication to Flask
3. Flask receives and stores the data in MySQL
4. The dashboard displays live readings in charts & tables
5. Light sensor automatically toggles LEDs (ON when dark, OFF when bright)

---

## 🧪 Testing

✅ Verified data transfer between **Arduino → Flask → MySQL**
✅ Tested light sensor (LED ON in darkness, OFF in brightness)
✅ Confirmed real-time updates on dashboard
✅ Validated login with correct/incorrect credentials

---

## 🧰 Tools Used

| Tool                   | Purpose                   |
| ---------------------- | ------------------------- |
| **Arduino IDE**        | Coding & testing hardware |
| **Visual Studio Code** | Flask web development     |
| **MySQL Workbench**    | Database management       |
| **Figma**              | Dashboard design          |
| **Lucid.app**          | ERD & database diagrams   |

---
**Written by:** Enas Hezabr
---
