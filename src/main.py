import pygame
import time
from queue import PriorityQueue
import config as cfg

class Node:
    def __init__(self, row, col, width, total_rows):
        self.row = row
        self.col = col
        self.x = row * width
        self.y = col * width
        self.color = cfg.DEFAULT_NODE_COLOR
        self.neighbors = []
        self.width = width
        self.total_rows = total_rows

    def get_pos(self): return self.row, self.col
    def is_barrier(self): return self.color == cfg.WALL_COLOR
    def is_start(self): return self.color == cfg.START_COLOR
    def is_end(self): return self.color == cfg.END_COLOR

    def reset(self): self.color = cfg.DEFAULT_NODE_COLOR
    def make_start(self): self.color = cfg.START_COLOR
    def make_closed(self): self.color = cfg.CLOSED_SET_COLOR
    def make_open(self): self.color = cfg.OPEN_SET_COLOR
    def make_barrier(self): self.color = cfg.WALL_COLOR
    def make_end(self): self.color = cfg.END_COLOR
    def make_path(self): self.color = cfg.PATH_COLOR

    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))

    def update_neighbors(self, grid):
        self.neighbors = []
        if self.row < self.total_rows - 1 and not grid[self.row + 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row + 1][self.col]) # DOWN
        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row - 1][self.col]) # UP
        if self.col < self.total_rows - 1 and not grid[self.row][self.col + 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col + 1]) # RIGHT
        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col - 1]) # LEFT

    def __lt__(self, other):
        return False


class PathfindingVisualizer:
    def __init__(self, width, rows):
        pygame.init()
        self.width = width
        self.rows = rows
        self.win = pygame.display.set_mode((width, width))
        pygame.display.set_caption("Pathfinding Algorithm Visualizer: [A] for A* | [D] for Dijkstra")

        self.grid = self.make_grid()
        self.start = None
        self.end = None
        self.clock = pygame.time.Clock()

    def make_grid(self):
        grid = []
        gap = self.width // self.rows
        for i in range(self.rows):
            grid.append([])
            for j in range(self.rows):
                grid[i].append(Node(i, j, gap, self.rows))
        return grid

    def draw(self):
        self.win.fill(cfg.WALL_COLOR)
        for row in self.grid:
            for node in row:
                node.draw(self.win)
        
        gap = self.width // self.rows
        for i in range(self.rows):
            pygame.draw.line(self.win, cfg.GRID_LINE_COLOR, (0, i * gap), (self.width, i * gap))
            pygame.draw.line(self.win, cfg.GRID_LINE_COLOR, (i * gap, 0), (i * gap, self.width))
        pygame.display.update()

    def get_clicked_pos(self, pos):
        gap = self.width // self.rows
        y, x = pos
        return y // gap, x // gap

    def h_metric(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return abs(x1 - x2) + abs(y1 - y2) # Manhattan distance

    def animate_path(self, came_from, current):
        path = []
        while current in came_from:
            current = came_from[current]
            if current != self.start:
                path.append(current)
        
        for node in reversed(path):
            node.make_path()
            self.draw()
            pygame.time.delay(15) 

    def algorithm(self, mode="A*"):
        start_time = time.time()
        nodes_explored = 0
        count = 0
        
        open_set = PriorityQueue()
        open_set.put((0, count, self.start))
        came_from = {}
        
        g_score = {node: float("inf") for row in self.grid for node in row}
        g_score[self.start] = 0
        f_score = {node: float("inf") for row in self.grid for node in row}
        
        # Dijkstra bypasses heuristic tracking entirely
        f_score[self.start] = 0 if mode == "Dijkstra" else self.h_metric(self.start.get_pos(), self.end.get_pos())
        open_set_hash = {self.start}

        while not open_set.empty():
            self.clock.tick(cfg.TARGET_FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None

            current = open_set.get()[2]
            open_set_hash.remove(current)
            nodes_explored += 1

            if current == self.end:
                self.animate_path(came_from, self.end)
                self.end.make_end()
                self.start.make_start()
                
                elapsed_time = (time.time() - start_time) * 1000
                print(f"\n[Algorithm - {mode}]")
                print(f"  Execution Runtime : {elapsed_time:.2f} ms")
                print(f"  Total Space Explored : {nodes_explored} Nodes")
                return True

            for neighbor in current.neighbors:
                temp_g_score = g_score[current] + 1

                if temp_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = temp_g_score
                    
                    h_val = 0 if mode == "Dijkstra" else self.h_metric(neighbor.get_pos(), self.end.get_pos())
                    f_score[neighbor] = temp_g_score + h_val
                    
                    if neighbor not in open_set_hash:
                        count += 1
                        open_set.put((f_score[neighbor], count, neighbor))
                        open_set_hash.add(neighbor)
                        if neighbor != self.end:
                            neighbor.make_open()

            self.draw()
            if current != self.start:
                current.make_closed()

        print(f"\nNo valid path to target found via {mode}.")
        return False

    def run_loop(self):
        run = True
        while run:
            if not pygame.get_init():
                break

            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    break

                if pygame.mouse.get_pressed()[0]:  # LEFT CLICK
                    row, col = self.get_clicked_pos(pygame.mouse.get_pos())
                    if 0 <= row < self.rows and 0 <= col < self.rows:
                        node = self.grid[row][col]
                        if not self.start and node != self.end:
                            self.start = node
                            self.start.make_start()
                        elif not self.end and node != self.start:
                            self.end = node
                            self.end.make_end()
                        elif node != self.end and node != self.start:
                            node.make_barrier()

                elif pygame.mouse.get_pressed()[2]:  # RIGHT CLICK
                    row, col = self.get_clicked_pos(pygame.mouse.get_pos())
                    if 0 <= row < self.rows and 0 <= col < self.rows:
                        node = self.grid[row][col]
                        node.reset()
                        if node == self.start: self.start = None
                        elif node == self.end: self.end = None

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a and self.start and self.end: # Run A*
                        for row in self.grid:
                            for node in row: node.update_neighbors(self.grid)
                        if self.algorithm(mode="A*") is None:
                            run = False
                            break

                    if event.key == pygame.K_d and self.start and self.end: # Run Dijkstra
                        for row in self.grid:
                            for node in row: node.update_neighbors(self.grid)
                        if self.algorithm(mode="Dijkstra") is None:
                            run = False
                            break

                    if event.key == pygame.K_c:
                        self.start = None
                        self.end = None
                        self.grid = self.make_grid()

        pygame.quit()

if __name__ == "__main__":
    app = PathfindingVisualizer(width=cfg.WIDTH, rows=cfg.ROWS)
    app.run_loop()
