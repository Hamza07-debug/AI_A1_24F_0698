## AI Pathfinder – Uninformed Search Visualizer

This is a small Python project where I made a grid based pathfinder using Pygame.  
The goal is to show how different uninformed search algorithms move on a 2D grid to reach a target.

---

## 1. Project Description

The program creates a square grid with:
- one **start** cell
- one **target** cell
- random **static walls**
- random **dynamic obstacles** during the run

The app tries to find a path from start to target and shows each step on the screen.  
The window title is `GOOD PERFORMANCE TIME APP`.

---

## 2. Features

- 2D grid (20x20) with clear colors for each cell type
- Static walls generated at the start
- Dynamic obstacles that can appear while searching
- If the path gets blocked, the search **re-plans** from the current agent position
- Step-by-step visualization (you can see the search exploring the grid)
- Header shows:
  - current algorithm name
  - explored node count
  - time taken in ms
  - depth (for DLS / IDDFS)
  - path length
  - a "Target Reached" message when goal is found

---

## 3. Algorithms Implemented

All algorithms use the same movement order (Up, Right, Down, Down-Right, Left, Up-Left, Top-Right, Bottom-Left).

- **BFS** – Breadth First Search  
- **DFS** – Depth First Search  
- **UCS** – Uniform Cost Search (all edge costs = 1)  
- **DLS** – Depth Limited Search  
- **IDDFS** – Iterative Deepening Depth First Search  
- **Bidirectional Search** – search from start and target at the same time

---

## 4. How to Install and Run

1. Make sure you have **Python 3** installed.
2. Install Pygame:

   ```bash
   pip install pygame
   ```

3. Go to the project folder in terminal:

   ```bash
   cd "D:\Hamza\FAST\4th Semester\AI\AI_A1_24F_0698"
   ```

4. Run the program:

   ```bash
   python main.py
   ```

5. In the console, choose the algorithm by number (1–6).  
   The Pygame window will open and start the selected search.

---

## 5. Controls

Inside the Pygame window:
- **Q** or **Esc** – quit the window

All other control (algorithm choice) is done in the console before Pygame starts.

---

## 6. Example Output

When you run an algorithm, you will see:
- Green start cell and red target cell
- Static black walls and new walls appearing randomly over time
- Blue frontier cells (on the border of exploration)
- Yellow explored cells
- Purple final path
- Header on top with live stats (explored, time, depth, path length)
- A small legend panel on the right explaining the colors

You can take screenshots of different algorithms and different maps for your report.

---

## 7. Simple Project Structure

The project is kept very small on purpose:

- `main.py` – all the code:
  - grid setup and drawing
  - user input for algorithm choice
  - BFS, DFS, UCS, DLS, IDDFS, Bidirectional Search
  - dynamic obstacle handling and re-planning
  - Pygame visualization
- `report.pdf` – assignment report (written separately)

Everything important for running and testing the pathfinder is inside `main.py`.

