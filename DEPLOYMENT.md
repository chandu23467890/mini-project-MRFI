# MRFI - Standalone Deployment Guide

## 🚀 Run MRFI Without VS Code - Phone Compatible

### **Quick Start (3 Steps)**

1. **Double-click `start_mrfi.bat`** (Windows) or `start_mrfi.sh` (Mac/Linux)
2. **Open browser** and go to the URL shown
3. **Login** with test credentials

---

## 📱 Mobile Phone Access

### **Method 1: WiFi Network (Recommended)**
1. **Run MRFI** on your computer using `start_mrfi.bat`
2. **Connect phone** to the same WiFi network
3. **Open browser** on phone and go to the IP address shown
4. **Login** and use MRFI on your phone!

### **Method 2: Direct Connection**
- The deployment script will show your local IP address
- Use that IP address on your phone: `http://YOUR_IP:5000`

---

## 🖥️ Computer Setup

### **Windows Users**
```bash
# 1. Open Command Prompt in the MRFI folder
cd c:\Users\ThatipartiChandu\Documents\Diabaties-MRFI

# 2. Run the deployment script
python deploy.py

# 3. Start MRFI
start_mrfi.bat
```

### **Mac/Linux Users**
```bash
# 1. Open Terminal in the MRFI folder
cd /path/to/Diabaties-MRFI

# 2. Run the deployment script
python3 deploy.py

# 3. Start MRFI
./start_mrfi.sh
```

---

## 📋 Requirements

### **Must Have:**
- ✅ **Python 3.7+** installed on your computer
- ✅ **Internet connection** (for first-time setup)
- ✅ **Modern browser** (Chrome, Safari, Firefox)

### **Optional:**
- 📱 **Smartphone** for mobile access
- 🌐 **WiFi network** for phone access

---

## 🔧 Installation Steps

### **Step 1: Install Python (if not installed)**
- **Windows**: Download from https://python.org/downloads/
- **Mac**: Already installed, or install from python.org
- **Linux**: `sudo apt-get install python3` (Ubuntu/Debian)

### **Step 2: Deploy MRFI**
```bash
# Navigate to MRFI folder
cd c:\Users\ThatipartiChandu\Documents\Diabaties-MRFI

# Run deployment (automatic setup)
python deploy.py
```

### **Step 3: Start MRFI**
```bash
# Windows
start_mrfi.bat

# Mac/Linux
./start_mrfi.sh
```

---

## 🌐 Access URLs

After starting MRFI, you'll see:

### **Computer Access**
- **Local**: http://localhost:5000
- **Network**: http://YOUR_IP:5000

### **Phone Access**
1. **Connect to same WiFi**
2. **Open browser**
3. **Go to**: http://YOUR_COMPUTER_IP:5000
4. **Login and use MRFI**

---

## 👤 Test Users

Use these accounts to test MRFI:

| Email | Password |
|-------|----------|
| sarah.j@example.com | password123 |
| raj.p@example.com | password123 |
| maria.g@example.com | password123 |
| james.c@example.com | password123 |
| amanda.w@example.com | password123 |

---

## 📱 Mobile Features

### **Phone Optimizations:**
- ✅ **Touch-friendly buttons** (44px minimum)
- ✅ **Responsive design** for all screen sizes
- ✅ **No zoom required** on mobile
- ✅ **Fast loading** on mobile networks
- ✅ **Full functionality** on phones

### **Mobile Experience:**
- 📊 **Dashboard** adapts to phone screen
- 📈 **Charts** work perfectly on mobile
- ➕ **Easy measurement logging**
- 🔄 **Real-time updates** on phone

---

## 🛠️ Troubleshooting

### **Python Not Found**
```bash
# Install Python first
# Windows: Download from python.org
# Mac: brew install python3
# Linux: sudo apt-get install python3
```

### **Port Already in Use**
- **Close other applications** using port 5000
- **Or restart your computer**
- **MRFI will auto-find available ports**

### **Phone Can't Connect**
1. **Check WiFi connection** - both devices on same network
2. **Firewall settings** - allow Python through firewall
3. **Use correct IP address** - shown when starting MRFI
4. **Try different browser** on phone

### **Dependencies Missing**
```bash
# Install missing packages automatically
python deploy.py
```

---

## 🎯 What MRFI Can Do on Phone

### **Full Mobile Functionality:**
- 📊 **View resonance field dashboard**
- 📈 **Track metabolic stability**
- ➕ **Log measurements**
- 📱 **Get recommendations**
- 🔄 **Real-time updates**
- 💾 **Save data securely**

### **Phone-Specific Features:**
- 📱 **Touch-optimized interface**
- 📊 **Mobile-friendly charts**
- 🔐 **Secure login**
- 💚 **Beautiful green theme**
- ⚡ **Fast performance**

---

## 🚀 Production Deployment

### **For Advanced Users:**
```bash
# Set production environment
export FLASK_ENV=production

# Use production database
export DATABASE_URL=postgresql://user:pass@localhost/mrfi

# Start with production settings
python run.py
```

---

## 📞 Support

### **Common Issues:**
1. **Python not installed** → Install Python first
2. **Dependencies missing** → Run `python deploy.py`
3. **Phone can't connect** → Check WiFi and IP address
4. **Port conflict** → Restart computer or close other apps

### **Get Help:**
- **Check error messages** in terminal
- **Ensure Python is working**: `python --version`
- **Verify network connection**
- **Try different browser**

---

## ✅ Success Checklist

When MRFI is working, you should see:

- [ ] **Green theme** throughout interface
- [ ] **MRFI branding** on all pages
- [ ] **Mobile responsive** design
- [ ] **Login works** with test users
- [ ] **Dashboard loads** with data
- [ ] **Charts display** correctly
- [ ] **Phone access** works via IP
- [ ] **Real-time updates** working

---

## 🎉 You're Ready!

**MRFI is now standalone and phone-compatible!**

1. **Run `start_mrfi.bat`** to start
2. **Access on computer** via localhost:5000
3. **Access on phone** via the IP address shown
4. **Enjoy MRFI anywhere!** 📱💚

No VS Code required - just double-click and go! 🚀
