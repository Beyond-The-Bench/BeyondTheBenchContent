---
title: AutoSailor – Click a map, send a boat
date: 2024-04-18
draft: false
tags:
  - Ollie
  - Ardupilot
  - Autonomy
  - Sailing
  - Sailboat
  - Python
  - Mapbox
  - Vite
author: Ollie
---

This project started as a way to control a sailboat by clicking on a map — and now, after a bit of hacking, simulating, and path-finding wizardry, it does exactly that.

Basically, I’ve built a system that lets you click a point on a map of a lake, and the boat figures out how to get there and sails off on its own. It’s all running in simulation for now, but the plan is to eventually use it on real hardware.

---

### The low-level stuff: ArduPilot firmware

On the boat side, everything’s built around a flight controller running [ArduPilot](https://ardupilot.org/)'s rover firmware — specifically its **sailboat mode**, which has a load of really useful features already baked in. Things like waypoint missions, tacking to reach upwind targets, and general autonomous control are all just there.

Since I don’t have a physical boat yet, I’ve been using the ArduPilot Software-In-The-Loop (SITL) platform to simulate everything. This lets me test the full system as if I had real hardware — super useful.

To get it running, I used:

`sim_vehicle.py -v Rover -f sailboat -l "51.6681611,-1.9201958,0,0" --speed 5`

This starts up a simulated sailboat on a custom lake location, running faster than real time so I’m not sat there watching it crawl across the screen.

![Image Description](/images/Pasted%20image%2020250412221820.webp)

---

### Talking to the boat: MavLink

All the communication with the boat happens over [MAVlink](https://mavlink.io/en/), which is a protocol used by loads of drones and other autonomous vehicles. In this case, I’m using it to send commands from a Python control script to the flight controller.

In a real-world setup, that script would probably be running on a Raspberry Pi, sending commands over a telemetry radio. For now, it's just running locally and talking to the SITL instance.

While I was setting this all up, I also used QGroundControl to double-check that the simulator and MavLink connections were working properly — it’s handy for visualising missions and status info.

![Image Description](/images/Pasted%20image%2020250412221853.webp)

---

### The brains: Python server with pathfinding

On the other end of the MavLink connection is a Python server using `pymavlink` to talk to the boat. This server also exposes an API that connects to the frontend.

The key features:

- It provides live boat position data to the frontend.

- It receives new destination coordinates when a user clicks on the map.

- It checks the destination is within a defined geo-fence.

- It runs an **A*** pathfinding algorithm to work out a safe route across the lake (even dodging around islands or obstacles).

- It then uploads that route as a list of waypoints to the boat.

![Image Description](/images/Pasted%20image%2020250412222508.webp)

Once uploaded, you just switch the boat into **AUTO** mode, and off it goes, following the waypoints.

---

### The frontend: Vite + MapboxGL

To make all this usable, I put together a simple frontend using [Vite](https://vitejs.dev/) and [MapboxGL](https://www.mapbox.com/). It overlays a custom image of the lake on the map, which makes it look cleaner and more usable than default satellite views.

The frontend connects to the Python server via WebSockets to:

- Show live position updates from the boat

- Send new destination clicks back to the server


Click a spot on the map → route gets planned → boat sails there. Easy.

![Image Description](/images/Pasted%20image%2020250412222320.webp)

---

### What’s next?

It all works pretty well for now, but there’s still plenty of stuff I want to improve:

- It’d be nice to show the boat’s current mode in the UI — sometimes it doesn’t move because it’s not armed or not in AUTO, and that’s not always obvious.

- Pathfinding could be made smarter and more efficient. ![Image Description](/images/Pasted%20image%2020250412222535.webp)

- A visual tool to define the geo-fence would make setup easier, especially when moving to different lakes or test areas.


But as a prototype? It does the job. Once we’ve got real hardware, this should make it way easier to test and demo autonomous sailing logic in a clean, interactive way.

---

If you’re curious, the full repo’s up here:  
👉 [AutoSailor on GitHub](https://github.com/Ollie-White/AutoSailor.git)

More to come when it hits the water.

---

### Technologies used:
-  [Vite](https://vitejs.dev/)
-  [MapboxGL](https://www.mapbox.com/)
-  [ArduPilot](https://ardupilot.org/)
-  [MAVlink](https://mavlink.io/en/)
- Python
