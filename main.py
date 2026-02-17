import pygame
import random
import heapq
import sys

# simple pathfinding visualizer in one file

# basic window and grid settings
WIDTH = 900
HEIGHT = 750

ROWS = 20
COLS = 20
CELL_SIZE = 30

HEADER_HEIGHT = 70
PADDING = 30
RIGHT_PANEL_WIDTH = 220

GRID_WIDTH = CELL_SIZE * COLS
GRID_HEIGHT = CELL_SIZE * ROWS
LEFT_AREA_WIDTH = WIDTH - RIGHT_PANEL_WIDTH
GRID_OFFSET_X = (LEFT_AREA_WIDTH - GRID_WIDTH) // 2
GRID_OFFSET_Y = HEADER_HEIGHT + PADDING

STATIC_WALL_PROB = 0.23
DYNAMIC_WALL_PROB = 0.02

DELAY_MS = 55  # delay between animation steps

# cell types
EMPTY = 0
WALL = 1

# colors for drawing
BG_COLOR = (25, 25, 25)
HEADER_COLOR = (18, 18, 18)
EMPTY_COLOR = (215, 215, 215)
GRID_LINE_COLOR = (190, 190, 190)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (70, 150, 240)
YELLOW = (255, 225, 60)
PURPLE = (185, 60, 250)

# movement order (must follow given order from assignment)
DIRS = [
    (-1, 0),   # Up
    (0, 1),    # Right
    (1, 0),    # Down
    (1, 1),    # Down-Right
    (0, -1),   # Left
    (-1, -1),  # Up-Left
    (-1, 1),   # Top-Right
    (1, -1)    # Bottom-Left
]

screen = None
clock = None
font = None
font_big = None
search_time_ms = 0
current_depth_str = "-"
path_length = 0
target_reached = False

# grid and some global state
grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
start = None
target = None
agent_pos = None

frontier_set = set()
explored_set = set()
path_set = set()


def inside_grid(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def generate_random_grid(scenario="random"):
    global grid, start, target, agent_pos
    # make empty grid
    grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

    if scenario == "best":
        # best case: no walls and start/target are close
        for r in range(ROWS):
            for c in range(COLS):
                grid[r][c] = EMPTY
        start = (10, 10)
        target = (10, 12)

    elif scenario == "worst":
        # worst case: many walls and far start/target
        for r in range(ROWS):
            for c in range(COLS):
                if random.random() < 0.35:
                    grid[r][c] = WALL
                else:
                    grid[r][c] = EMPTY
        start = (0, 0)
        target = (ROWS - 1, COLS - 1)
        grid[start[0]][start[1]] = EMPTY
        grid[target[0]][target[1]] = EMPTY

    else:
        # original random generation
        for r in range(ROWS):
            for c in range(COLS):
                if random.random() < STATIC_WALL_PROB:
                    grid[r][c] = WALL

        while True:
            sr = random.randint(0, ROWS - 1)
            sc = random.randint(0, COLS - 1)
            if grid[sr][sc] == EMPTY:
                start = (sr, sc)
                break

        while True:
            tr = random.randint(0, ROWS - 1)
            tc = random.randint(0, COLS - 1)
            if grid[tr][tc] == EMPTY and (tr, tc) != start:
                target = (tr, tc)
                break

    agent_pos = start
    return grid, start, target


def draw_grid(current_algorithm_name=""):
    screen.fill(BG_COLOR)

    pygame.draw.rect(screen, HEADER_COLOR, (0, 0, WIDTH, HEADER_HEIGHT))

    algo_text = font_big.render(current_algorithm_name, True, (230, 230, 230))
    screen.blit(algo_text, (20, 15))

    info_text1 = font.render(f"Explored: {len(explored_set)}", True, (210, 210, 210))
    info_text2 = font.render(f"Time: {search_time_ms} ms", True, (210, 210, 210))
    depth_text = font.render(f"Depth: {current_depth_str}", True, (210, 210, 210))
    path_text = font.render(f"Path: {path_length}", True, (210, 210, 210))
    screen.blit(info_text1, (20, HEADER_HEIGHT - 25))
    screen.blit(info_text2, (180, HEADER_HEIGHT - 25))
    screen.blit(depth_text, (340, HEADER_HEIGHT - 25))
    screen.blit(path_text, (460, HEADER_HEIGHT - 25))

    if target_reached:
        status_text = font.render("Target Reached", True, (0, 230, 0))
        screen.blit(status_text, (650, HEADER_HEIGHT - 25))

    for r in range(ROWS):
        for c in range(COLS):
            color = EMPTY_COLOR
            if grid[r][c] == WALL:
                color = BLACK

            if (r, c) in explored_set:
                color = YELLOW
            if (r, c) in frontier_set:
                color = BLUE
            if (r, c) in path_set:
                color = PURPLE

            if (r, c) == start:
                color = GREEN
            if (r, c) == target:
                color = RED
            if (r, c) == agent_pos:
                color = GREEN

            pygame.draw.rect(
                screen,
                color,
                (
                    GRID_OFFSET_X + c * CELL_SIZE,
                    GRID_OFFSET_Y + r * CELL_SIZE,
                    CELL_SIZE - 1,
                    CELL_SIZE - 1,
                )
            )

    for r in range(ROWS + 1):
        y = GRID_OFFSET_Y + r * CELL_SIZE
        pygame.draw.line(screen, GRID_LINE_COLOR, (GRID_OFFSET_X, y), (GRID_OFFSET_X + GRID_WIDTH, y), 1)
    for c in range(COLS + 1):
        x = GRID_OFFSET_X + c * CELL_SIZE
        pygame.draw.line(screen, GRID_LINE_COLOR, (x, GRID_OFFSET_Y), (x, GRID_OFFSET_Y + GRID_HEIGHT), 1)

    legend_items = [
        ("Empty", EMPTY_COLOR),
        ("Wall", BLACK),
        ("Start", GREEN),
        ("Target", RED),
        ("Frontier", BLUE),
        ("Explored", YELLOW),
        ("Path", PURPLE),
    ]

    legend_width = RIGHT_PANEL_WIDTH - 20
    legend_height = 24 * len(legend_items) + 24
    panel_x = WIDTH - RIGHT_PANEL_WIDTH
    panel_y = HEADER_HEIGHT
    legend_x = panel_x + 10
    legend_y = panel_y + 20

    panel_surface = pygame.Surface((RIGHT_PANEL_WIDTH, HEIGHT - HEADER_HEIGHT), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 160))
    screen.blit(panel_surface, (panel_x, panel_y))

    legend_surface = pygame.Surface((legend_width, legend_height), pygame.SRCALPHA)
    legend_surface.fill((0, 0, 0, 0))
    screen.blit(legend_surface, (legend_x, legend_y))

    for i, (name, color) in enumerate(legend_items):
        y = legend_y + 8 + i * 24
        pygame.draw.rect(screen, color, (legend_x + 6, y, 20, 20))
        txt = font.render(name, True, (235, 235, 235))
        screen.blit(txt, (legend_x + 32, y + 1))


def draw_step(title):
    """small helper so I don't repeat these three lines everywhere"""
    draw_grid(title)
    pygame.display.flip()
    pygame.time.delay(DELAY_MS)


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


def maybe_spawn_dynamic_wall():
    if random.random() < DYNAMIC_WALL_PROB:
        tries = 0
        while tries < 1000:
            r = random.randint(0, ROWS - 1)
            c = random.randint(0, COLS - 1)
            if grid[r][c] == EMPTY and (r, c) != start and (r, c) != target and (r, c) != agent_pos:
                grid[r][c] = WALL
                break
            tries += 1


def reconstruct_path(parents, goal):
    path = []
    cur = goal
    while cur in parents and cur is not None:
        path.append(cur)
        cur = parents[cur]
    path.reverse()
    return path


def bfs_search(s, t, algo_name="BFS"):
    global frontier_set, explored_set, path_set, current_depth_str
    frontier_set = set()
    explored_set = set()
    path_set = set()
    current_depth_str = "-"

    from collections import deque
    q = deque()
    q.append(s)
    parents = {s: None}
    visited = {s}
    frontier_set.add(s)

    while q:
        handle_events()
        maybe_spawn_dynamic_wall()

        current = q.popleft()
        frontier_set.discard(current)
        explored_set.add(current)

        draw_step(algo_name)

        if current == t:
            return reconstruct_path(parents, t)

        for dr, dc in DIRS:
            nr = current[0] + dr
            nc = current[1] + dc
            if inside_grid(nr, nc) and grid[nr][nc] != WALL:
                neighbor = (nr, nc)
                if neighbor not in visited:
                    visited.add(neighbor)
                    parents[neighbor] = current
                    q.append(neighbor)
                    frontier_set.add(neighbor)

    return []


def dfs_search(s, t, algo_name="DFS"):
    global frontier_set, explored_set, path_set, current_depth_str
    frontier_set = set()
    explored_set = set()
    path_set = set()
    current_depth_str = "-"

    stack = [s]
    parents = {s: None}
    visited = set()
    frontier_set.add(s)

    while stack:
        handle_events()
        maybe_spawn_dynamic_wall()

        current = stack.pop()
        frontier_set.discard(current)
        if current in visited:
            continue
        visited.add(current)
        explored_set.add(current)

        draw_step(algo_name)

        if current == t:
            return reconstruct_path(parents, t)

        neighbors = []
        for dr, dc in DIRS:
            nr = current[0] + dr
            nc = current[1] + dc
            if inside_grid(nr, nc) and grid[nr][nc] != WALL:
                neighbor = (nr, nc)
                if neighbor not in visited:
                    neighbors.append(neighbor)

        for neighbor in reversed(neighbors):
            if neighbor not in visited:
                stack.append(neighbor)
                frontier_set.add(neighbor)
                if neighbor not in parents:
                    parents[neighbor] = current

    return []


def ucs_search(s, t, algo_name="UCS"):
    global frontier_set, explored_set, path_set, current_depth_str
    frontier_set = set()
    explored_set = set()
    path_set = set()
    current_depth_str = "-"

    pq = []
    heapq.heappush(pq, (0, s))
    parents = {s: None}
    cost = {s: 0}
    visited = set()
    frontier_set.add(s)

    while pq:
        handle_events()
        maybe_spawn_dynamic_wall()

        g, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)

        frontier_set.discard(current)
        explored_set.add(current)

        draw_step(algo_name)

        if current == t:
            return reconstruct_path(parents, t)

        for dr, dc in DIRS:
            nr = current[0] + dr
            nc = current[1] + dc
            if inside_grid(nr, nc) and grid[nr][nc] != WALL:
                neighbor = (nr, nc)
                new_cost = g + 1
                if neighbor not in cost or new_cost < cost[neighbor]:
                    cost[neighbor] = new_cost
                    parents[neighbor] = current
                    heapq.heappush(pq, (new_cost, neighbor))
                    frontier_set.add(neighbor)

    return []


def dls_recursive(current, t, limit, parents, algo_name):
    handle_events()
    maybe_spawn_dynamic_wall()

    explored_set.add(current)

    draw_step(algo_name)

    if current == t:
        return True

    if limit == 0:
        return False

    for dr, dc in DIRS:
        nr = current[0] + dr
        nc = current[1] + dc
        if inside_grid(nr, nc) and grid[nr][nc] != WALL:
            neighbor = (nr, nc)
            if neighbor not in explored_set:
                parents[neighbor] = current
                if dls_recursive(neighbor, t, limit - 1, parents, algo_name):
                    return True

    return False


def dls_search(s, t, depth_limit=30, algo_name="DLS"):
    global frontier_set, explored_set, path_set, current_depth_str
    frontier_set = set()
    explored_set = set()
    path_set = set()

    parents = {s: None}
    frontier_set.add(s)
    current_depth_str = str(depth_limit)

    found = dls_recursive(s, t, depth_limit, parents, algo_name)

    if found:
        return reconstruct_path(parents, t)
    else:
        return []


def iddfs_search(s, t, max_depth=50, algo_name="IDDFS"):
    global frontier_set, explored_set, path_set, current_depth_str

    for depth in range(max_depth + 1):
        frontier_set = set()
        explored_set = set()
        path_set = set()
        parents = {s: None}
        frontier_set.add(s)
        current_depth_str = str(depth)

        def dls_id(current, t, limit):
            handle_events()
            maybe_spawn_dynamic_wall()

            explored_set.add(current)
            draw_step(algo_name)

            if current == t:
                return True

            if limit == 0:
                return False

            for dr, dc in DIRS:
                nr = current[0] + dr
                nc = current[1] + dc
                if inside_grid(nr, nc) and grid[nr][nc] != WALL:
                    neighbor = (nr, nc)
                    if neighbor not in explored_set:
                        parents[neighbor] = current
                        if dls_id(neighbor, t, limit - 1):
                            return True
            return False

        if dls_id(s, t, depth):
            return reconstruct_path(parents, t)

    return []


def bidirectional_search(s, t, algo_name="Bidirectional"):
    global frontier_set, explored_set, path_set, current_depth_str
    frontier_set = set()
    explored_set = set()
    path_set = set()
    current_depth_str = "-"

    from collections import deque

    q_s = deque([s])
    q_t = deque([t])
    parent_s = {s: None}
    parent_t = {t: None}
    visited_s = {s}
    visited_t = {t}

    frontier_set.update(q_s)
    frontier_set.update(q_t)

    meeting = None

    while q_s and q_t:
        handle_events()
        maybe_spawn_dynamic_wall()

        if q_s:
            current = q_s.popleft()
            frontier_set.discard(current)
            explored_set.add(current)

            draw_step(algo_name)

            if current in visited_t:
                meeting = current
                break

            for dr, dc in DIRS:
                nr = current[0] + dr
                nc = current[1] + dc
                if inside_grid(nr, nc) and grid[nr][nc] != WALL:
                    neighbor = (nr, nc)
                    if neighbor not in visited_s:
                        visited_s.add(neighbor)
                        parent_s[neighbor] = current
                        q_s.append(neighbor)
                        frontier_set.add(neighbor)

        handle_events()
        maybe_spawn_dynamic_wall()

        if q_t:
            current = q_t.popleft()
            frontier_set.discard(current)
            explored_set.add(current)

            draw_step(algo_name)

            if current in visited_s:
                meeting = current
                break

            for dr, dc in DIRS:
                nr = current[0] + dr
                nc = current[1] + dc
                if inside_grid(nr, nc) and grid[nr][nc] != WALL:
                    neighbor = (nr, nc)
                    if neighbor not in visited_t:
                        visited_t.add(neighbor)
                        parent_t[neighbor] = current
                        q_t.append(neighbor)
                        frontier_set.add(neighbor)

    if meeting is None:
        return []

    path1 = []
    cur = meeting
    while cur is not None:
        path1.append(cur)
        cur = parent_s[cur]
    path1.reverse()

    path2 = []
    cur = meeting
    while cur is not None:
        path2.append(cur)
        cur = parent_t[cur]
    path2 = path2[1:]

    full_path = path1 + path2
    return full_path


def move_agent_along_path(path, algo_func, algo_name):
    global agent_pos, path_set, frontier_set, explored_set, search_time_ms, target_reached

    if not path:
        return

    for i in range(1, len(path)):
        handle_events()
        maybe_spawn_dynamic_wall()

        blocked = False
        for j in range(i, len(path)):
            r, c = path[j]
            if grid[r][c] == WALL:
                blocked = True
                break

        if blocked:
            frontier_set = set()
            explored_set = set()
            path_set = set()
            draw_step(algo_name + " (replan)")

            start_ticks = pygame.time.get_ticks()
            new_path = algo_func(agent_pos, target, algo_name)
            search_time_ms = pygame.time.get_ticks() - start_ticks
            path_set = set(new_path)
            draw_step(algo_name + " (new path)")

            move_agent_along_path(new_path, algo_func, algo_name)
            return

        agent_pos = path[i]
        path_set = set(path[:i + 1])

        draw_step(algo_name + " (move)")

        if agent_pos == target:
            target_reached = True
            break


def main():
    global frontier_set, explored_set, path_set, agent_pos, screen, clock, font, font_big, search_time_ms, current_depth_str, path_length, target_reached

    print("Choose Algorithm:")
    print("1 - BFS")
    print("2 - DFS")
    print("3 - UCS")
    print("4 - DLS")
    print("5 - IDDFS")
    print("6 - Bidirectional")
    choice = input("Enter number: ").strip()

    algo_func = None
    algo_name = ""

    if choice == "1":
        algo_func = bfs_search
        algo_name = "BFS"
    elif choice == "2":
        algo_func = dfs_search
        algo_name = "DFS"
    elif choice == "3":
        algo_func = ucs_search
        algo_name = "UCS"
    elif choice == "4":
        algo_func = lambda s, t, name: dls_search(s, t, depth_limit=40, algo_name="DLS")
        algo_name = "DLS"
    elif choice == "5":
        algo_func = lambda s, t, name: iddfs_search(s, t, max_depth=50, algo_name="IDDFS")
        algo_name = "IDDFS"
    elif choice == "6":
        algo_func = bidirectional_search
        algo_name = "Bidirectional"
    else:
        print("Invalid choice.")
        return

    # ask for scenario until user gives a valid one
    while True:
        scenario = input("Choose scenario (random/best/worst): ").lower()
        if scenario in ["random", "best", "worst"]:
            break
        else:
            print("Invalid input. Please enter random, best, or worst.")

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("GOOD PERFORMANCE TIME APP")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 18)
    font_big = pygame.font.SysFont("arial", 26)

    grid_obj, start_pos, target_pos = generate_random_grid(scenario)
    # keep using globals for algorithms
    grid[:] = grid_obj
    start = start_pos
    target = target_pos
    agent_pos = start

    current_depth_str = "-"
    path_length = 0
    target_reached = False
    draw_step(algo_name)

    search_time_ms = 0
    start_ticks = pygame.time.get_ticks()
    path = algo_func(agent_pos, target, algo_name)
    search_time_ms = pygame.time.get_ticks() - start_ticks
    path_length = len(path)
    path_set.update(path)
    draw_step(algo_name)

    move_agent_along_path(path, algo_func, algo_name)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False

        draw_grid(algo_name)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()



