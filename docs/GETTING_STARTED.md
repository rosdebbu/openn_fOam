# 🚀 Getting Started with OpenZess 3D Studio

Follow this guide to get **OpenZess 3D Studio** up and running on your local machine.

---

## 📋 Prerequisites
1. **Python 3.10+**: Ensure Python is added to your system `PATH`.
2. **Node.js 18+ & npm**: For building the frontend client.

---

## 🔧 Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/openn_fOam.git
cd openn_fOam
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Build the Web Studio Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## ⚡ Launching the Application

Simply run:
```bash
python main.py
```

### What Happens When You Launch:
1. The **FastAPI backend server** starts at `http://127.0.0.1:8000`.
2. Your default web browser automatically opens to `http://localhost:8000/studio/index.html`.
3. The **Three.js WebGL 3D Studio** initializes with the default 3D Room HVAC domain and Table obstacle.

---

## 🎮 Using OpenZess: First Simulation Walkthrough

1. **Pick an Object**:
   - In the left sidebar under the **🤖 AI Co-Pilot** tab, click a preset chip (e.g. **Submarine**, **Table**, **Chair**, **Room Heater**) or drag & drop a photo from your computer.
   - The AI vision module instantly detects the archetype and auto-configures the domain bounds and flow regime.

2. **Chat with the Co-Pilot**:
   - In the chat box at the bottom, type:
     ```text
     "Make the air velocity 3.0 m/s and set heater to 55°C"
     ```
   - Watch the Co-Pilot update the physical parameters and provide a fluid dynamics explanation.

3. **Run the 3D Simulation**:
   - Click the blue **🚀 Run 3D Simulation** button.
   - The 3D scene immediately renders fluid particle streamlines flowing around the 3D obstacle.

4. **Explore the 3D Viewport**:
   - **Rotate**: Left-click and drag anywhere on the 3D room.
   - **Zoom**: Scroll the mouse wheel.
   - **Cut-Planes**: Switch between **XY (Top)**, **XZ (Side)**, and **YZ (Front)** cross-sections and drag the **Position slider** to see internal temperature or pressure contours.
   - **Probing**: Hover your mouse over the room to see exact Velocity, Temperature, and Pressure values in the floating HUD.

5. **Download Production Files**:
   - Click **📦 OpenFOAM Case (.zip)** in the top bar to download the complete OpenFOAM case.
   - Click **📊 ParaView 3D (.vtk)** to download the VTK structured grid for post-processing in ParaView.
