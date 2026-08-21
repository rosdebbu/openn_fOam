# 🧠 AI Vision & Conversational Co-Pilot Layer

The **AI Layer** in OpenZess removes the barrier of manual CFD setup and dictionary coding by combining Computer Vision with an engineering-aware Natural Language Co-Pilot.

---

## 📸 1. Image-to-3D Ingestion & Voxelization

When a user uploads a 2D photograph of an everyday or industrial object:

```
2D Image Upload
      │
      ▼
Edge & Silhouette Extraction (Binary Contour Matrix)
      │
      ▼
Depth Estimation & Archetype Classification
      │
      ▼
3D Transverse Extrusion (SDF / Voxel Grid)
      │
      ▼
Immersed Solid Body in 3D Domain (Room/Tunnel)
```

### Archetypes & Detection Logic:
- **Marine Vessels (`submarine`)**: Streamlined prolate hulls with tower sails and stabilizer fins. Configures hydrodynamic water flow ($Re \approx 25,000$).
- **Interior Furniture (`table`, `chair`)**: Tabletop surfaces with 4 slender legs, backrests, and seat pans. Configures room HVAC ventilation airflow ($Re \approx 1,200$).
- **Thermal Heat Sources (`radiator`, `server_rack`)**: Solid heat-emitting blocks with surface temperature boundary conditions ($T_{source} \ge 50^\circ\text{C}$), generating natural Boussinesq thermal buoyancy plumes.
- **Vehicles (`car`)**: Aerodynamic bluff bodies with stagnation hoods, sloped windshields, and wake separation.

---

## 🤖 2. Conversational Co-Pilot (NLP)

The Co-Pilot allows engineers and students to converse naturally with the simulation engine:

### Supported Natural Language Commands:
| User Command Example | Action Taken by Co-Pilot | Physics Explained |
| :--- | :--- | :--- |
| *"Set inlet speed to 4.5 m/s"* | Updates $U_{inlet} = 4.5\text{ m/s}$ and recalculates Reynolds number $Re$. | Explains increase in dynamic pressure $q = \frac{1}{2}\rho U^2$ and wake turbulence. |
| *"Heat the radiator to 60°C"* | Sets $T_{heat} = 333.15\text{ K}$ ($60^\circ\text{C}$). | Explains upward thermal convection plume driven by $\beta g \Delta T$. |
| *"Simulate submarine in water"* | Switches domain to `water_channel`, updates fluid properties to liquid water. | Explains high-Reynolds boundary layer separation on hull and sail rudders. |
| *"Generate OpenFOAM case"* | Compiles all OpenFOAM v2312 dictionaries into a downloadable ZIP archive. | Explains boundary condition mapping across patches (`inlet`, `outlet`, `walls`). |
