import requests

class World:
    def __init__(self):
        self.grid_bounds = {"x_min": -5, "x_max": 5, "y_min": -5, "y_max": 5, "z_min": 0, "z_max": 2}
        self.player_pos = (0, 0, 1)  # Start at center, hills
        self.ollama_url = "http://localhost:11434/api/generate"
        # Persistent map: (x, y, z) -> (name, type)
        self.map = {
            (0, 0, 0): ("River Plain", "plain"),
            (0, 1, 0): ("North Meadow", "plain"),
            (0, -1, 0): ("South Grassland", "plain"),
            (1, 0, 0): ("East Village", "plain"),
            (-1, 0, 0): ("West Grove", "plain"),
            (0, 0, 1): ("Central Hill", "hill"),
            (0, 1, 1): ("Stone Circle Hill", "hill"),
            (0, -1, 1): ("South Ridge", "hill"),
            (1, 0, 1): ("East Slope", "hill"),
            (-1, 0, 1): ("West Knoll", "hill"),
            (0, 0, 2): ("Central Peak", "mountain"),
            (0, 1, 2): ("North Crag", "mountain"),
            (0, -1, 2): ("South Summit", "mountain"),
            (1, 0, 2): ("East Ridge", "mountain"),
            (-1, 0, 2): ("West Cliff", "mountain"),
        }
        # Fill unlisted coords with defaults based on Z
        for x in range(-5, 6):
            for y in range(-5, 6):
                for z in range(3):
                    if (x, y, z) not in self.map:
                        self.map[(x, y, z)] = (f"Unnamed {['Plain', 'Hill', 'Mountain'][z]}", ["plain", "hill", "mountain"][z])

    def ollama_narrate(self, prompt):
        payload = {
            "model": "gemma3:1b",
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error: {e} - The world fades to silence."

    def format_coords(self):
        x, y, z = self.player_pos
        return f"(x{x}, y{y}, z{z})"

    def get_nearby(self):
        x, y, z = self.player_pos
        nearby = {}
        directions = [("north", (0, 1, 0)), ("south", (0, -1, 0)), ("east", (1, 0, 0)), 
                      ("west", (-1, 0, 0)), ("up", (0, 0, 1)), ("down", (0, 0, -1))]
        for dir_name, (dx, dy, dz) in directions:
            nx, ny, nz = x + dx, y + dy, z + dz
            if (self.grid_bounds["x_min"] <= nx <= self.grid_bounds["x_max"] and
                self.grid_bounds["y_min"] <= ny <= self.grid_bounds["y_max"] and
                self.grid_bounds["z_min"] <= nz <= self.grid_bounds["z_max"]):
                nearby[dir_name] = self.map.get((nx, ny, nz), ("Unknown", "unknown"))
        return nearby

    def describe_location(self):
        x, y, z = self.player_pos
        name, terrain_type = self.map[(x, y, z)]
        nearby = self.get_nearby()
        nearby_text = ", ".join(f"{dir}: {n[0]}" for dir, n in nearby.items())
        prompt = (f"The player stands at ({x}, {y}, {z}) in a persistent world, at {name} ({terrain_type}). "
                  f"Describe this {terrain_type} naturally—grasses, trees, rivers, or peaks—"
                  f"and mention what’s visible nearby: {nearby_text}. Ask what they do next. "
                  f"End with '{self.format_coords()}'.")
        return self.ollama_narrate(prompt)

    def move(self, direction):
        x, y, z = self.player_pos
        if direction == "north" and y < self.grid_bounds["y_max"]:
            y += 1
        elif direction == "south" and y > self.grid_bounds["y_min"]:
            y -= 1
        elif direction == "east":
            x = (x + 1) if x < self.grid_bounds["x_max"] else self.grid_bounds["x_min"]  # Wrap east
        elif direction == "west":
            x = (x - 1) if x > self.grid_bounds["x_min"] else self.grid_bounds["x_max"]  # Wrap west
        elif direction == "up" and z < self.grid_bounds["z_max"]:
            z += 1
        elif direction == "down" and z > self.grid_bounds["z_min"]:
            z -= 1
        else:
            if direction == "up" and z == self.grid_bounds["z_max"]:
                prompt = (f"The player at {self.format_coords()} tries to move up, but a vast, unseen firmament "
                          f"blocks the way—an ancient dome above the mountains. Describe the scene and ask what they do next. "
                          f"End with '{self.format_coords()}'.")
            else:
                prompt = (f"The player at {self.format_coords()} tries to move {direction}, but the way is blocked—"
                          f"plains below at z0 or the world’s edge at y-5 or y5. Describe the scene and ask what they do next. "
                          f"End with '{self.format_coords()}'.")
            return self.ollama_narrate(prompt)
        self.player_pos = (x, y, z)
        return self.describe_location()

    def start(self):
        x, y, z = self.player_pos
        name, terrain_type = self.map[(x, y, z)]
        nearby = self.get_nearby()
        nearby_text = ", ".join(f"{dir}: {n[0]}" for dir, n in nearby.items())
        prompt = (f"Welcome a player to a vast, persistent world of plains, hills, and mountains, standing at the center "
                  f"({x}, {y}, {z}) at {name} ({terrain_type}). Describe this {terrain_type} naturally—"
                  f"plains to the east, mountains north, hills south, groves west, and options to descend—"
                  f"with a firmament barring the sky above. Mention nearby: {nearby_text}. Tell them to move "
                  f"'north', 'east', 'south', 'west', 'up', or 'down'. End with '{self.format_coords()}'.")
        return self.ollama_narrate(prompt)

    def update(self, player_input):
        directions = ["north", "east", "south", "west", "up", "down"]
        if player_input.lower() in directions:
            return self.move(player_input.lower())
        return "Move with 'north', 'east', 'south', 'west', 'up', or 'down' to explore."

# Game loop
world = World()
print(world.start())
while True:
    action = input("> ")
    if action:
        print(world.update(action))
