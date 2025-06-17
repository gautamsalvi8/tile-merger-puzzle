import pygame
import random
import sys
import time
import math
from pygame.locals import *

# Initialize pygame
pygame.init()

# Constants
GRID_SIZE = 4
CELL_SIZE = 100
MARGIN = 10
WINDOW_WIDTH = GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN
WINDOW_HEIGHT = GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN + 150
BACKGROUND_COLOR = (252, 247, 255)  # Light lavender background
GRID_COLOR = (149, 125, 173)  # Purple grid
EMPTY_CELL_COLOR = (200, 183, 219)  # Light purple cells
TEXT_COLOR = (75, 0, 130)  # Indigo text
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SELECTED_TILE_COLOR = (255, 140, 0, 180)  # Bright orange selection
SPECIAL_TILE_COLOR = (0, 191, 255)  # Deep sky blue for special tiles
TARGET_TILE_COLOR = (255, 215, 0)  # Gold color for target tiles

# Game states
STATE_PLAYING = 0
STATE_LEVEL_COMPLETE = 1
STATE_GAME_OVER = 2

# Enhanced vibrant color palette with extended values
TILE_COLORS = {
    2: (255, 229, 180),     # Peach
    4: (255, 191, 134),     # Light orange
    8: (255, 153, 102),     # Orange
    16: (255, 94, 91),      # Coral
    32: (255, 64, 129),     # Pink
    64: (224, 64, 251),     # Magenta
    100: (180, 70, 255),    # Bright purple (special for level 1)
    128: (124, 77, 255),    # Purple
    200: (100, 90, 255),    # Deep blue-purple (special for level 2)
    256: (83, 109, 254),    # Blue
    300: (50, 130, 255),    # Royal blue (special for level 3)
    400: (20, 170, 255),    # Azure (special for level 4)
    500: (0, 200, 255),     # Bright cyan (special for level 5)
    512: (0, 176, 255),     # Cyan
    600: (0, 210, 210),     # Turquoise (special for level 6)
    700: (0, 230, 180),     # Aquamarine (special for level 7)
    800: (20, 240, 160),    # Sea green (special for level 8)
    1024: (29, 233, 182),   # Teal
    2048: (118, 255, 122),  # Green
    4096: (253, 216, 53),   # Yellow
    8192: (255, 171, 64)    # Amber
}

# Function to get color for any tile value
def get_tile_color(value):
    if value in TILE_COLORS:
        return TILE_COLORS[value]
    
    # For values not in the dictionary, generate a color based on the value
    # This ensures we never use black and always have a vibrant color
    
    # For very large numbers, use logarithmic scaling to avoid color repetition
    if value > 8192:
        # Use log2 of the value to determine the hue
        log_value = math.log2(value)
        hue = (log_value * 20) % 360 / 360.0  # Cycle through hues based on log2
    else:
        # For smaller numbers, use direct value
        hue = (value % 360) / 360.0  # Use modulo to cycle through hues
    
    saturation = 0.7 + (value % 300) / 1000.0  # High saturation but vary slightly
    value_brightness = 0.9  # Keep brightness high for visibility
    
    # Convert HSV to RGB (simplified conversion)
    h = hue * 6
    i = int(h)
    f = h - i
    p = value_brightness * (1 - saturation)
    q = value_brightness * (1 - saturation * f)
    t = value_brightness * (1 - saturation * (1 - f))
    
    if i == 0:
        r, g, b = value_brightness, t, p
    elif i == 1:
        r, g, b = q, value_brightness, p
    elif i == 2:
        r, g, b = p, value_brightness, t
    elif i == 3:
        r, g, b = p, q, value_brightness
    elif i == 4:
        r, g, b = t, p, value_brightness
    else:
        r, g, b = value_brightness, p, q
    
    return (int(r * 255), int(g * 255), int(b * 255))

class Tile:
    def __init__(self, value, row, col, is_special=False):
        self.value = value
        self.row = row
        self.col = col
        self.target_row = row
        self.target_col = col
        self.x = MARGIN + col * (CELL_SIZE + MARGIN)
        self.y = MARGIN + row * (CELL_SIZE + MARGIN)
        self.target_x = self.x
        self.target_y = self.y
        self.merge_animation = 0
        self.moving = False
        self.merged_this_move = False
        self.selected = False
        self.is_special = is_special  # Flag for special tiles (previous level targets)
        self.is_target_tile = False   # Flag for tiles that match the current target
        self.glow_effect = 0  # For special tile animation

    def update(self, dt):
        # Update merge animation
        if self.merge_animation > 0:
            self.merge_animation = max(0, self.merge_animation - dt * 4)
        
        # Update glow effect for special tiles and target tiles
        if self.is_special or self.is_target_tile:
            self.glow_effect = (self.glow_effect + dt * 2) % (2 * math.pi)
        
        # Update movement
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < 2:  # Close enough to snap to target
                self.x = self.target_x
                self.y = self.target_y
                self.row = self.target_row
                self.col = self.target_col
                self.moving = False
            else:
                # Smooth movement
                self.x += dx * dt * 15
                self.y += dy * dt * 15

    def draw(self, screen, font):
        # Determine tile color
        if self.is_target_tile:
            # Gold color for target value tiles
            base_color = TARGET_TILE_COLOR
            # Add pulsing glow effect for target tiles
            glow_size = int(5 + 3 * math.sin(self.glow_effect))
            glow_surf = pygame.Surface((CELL_SIZE+glow_size*2, CELL_SIZE+glow_size*2), pygame.SRCALPHA)
            glow_color = (*TARGET_TILE_COLOR, 150)  # Gold with alpha
            pygame.draw.rect(glow_surf, glow_color,
                           (0, 0, CELL_SIZE+glow_size*2, CELL_SIZE+glow_size*2), 0, 10)
            screen.blit(glow_surf, (self.x-glow_size, self.y-glow_size))
        elif self.is_special:
            base_color = get_tile_color(self.value)  # Use the value's color for special tiles
            # Add pulsing glow effect for special tiles
            glow_size = int(5 + 3 * math.sin(self.glow_effect))
            glow_surf = pygame.Surface((CELL_SIZE+glow_size*2, CELL_SIZE+glow_size*2), pygame.SRCALPHA)
            glow_color = (*SPECIAL_TILE_COLOR, 150)  # Add alpha for transparency
            pygame.draw.rect(glow_surf, glow_color,
                           (0, 0, CELL_SIZE+glow_size*2, CELL_SIZE+glow_size*2), 0, 10)
            screen.blit(glow_surf, (self.x-glow_size, self.y-glow_size))
        else:
            base_color = get_tile_color(self.value)  # Use our function to get color for any value
        
        # Draw selection highlight
        if self.selected:
            select_surf = pygame.Surface((CELL_SIZE+10, CELL_SIZE+10), pygame.SRCALPHA)
            pygame.draw.rect(select_surf, SELECTED_TILE_COLOR,
                           (0, 0, CELL_SIZE+10, CELL_SIZE+10), 0, 8)
            screen.blit(select_surf, (self.x-5, self.y-5))
        
        # Draw main tile with merge animation
        anim_scale = 1 + 0.1 * self.merge_animation
        anim_offset = (CELL_SIZE * (anim_scale - 1)) / 2
        pygame.draw.rect(screen, base_color,
                       (self.x - anim_offset, self.y - anim_offset,
                        CELL_SIZE * anim_scale, CELL_SIZE * anim_scale), 0, 5)

        # Draw value text
        # Determine text color based on background brightness for better contrast
        r, g, b = base_color
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = WHITE if brightness < 180 else TEXT_COLOR  # Use white text on dark backgrounds
        
        # Adjust font size based on the number of digits
        value_str = str(self.value)
        if len(value_str) <= 2:
            font_size = 36
        elif len(value_str) <= 3:
            font_size = 32
        elif len(value_str) <= 4:
            font_size = 28
        elif len(value_str) <= 5:
            font_size = 24
        elif len(value_str) <= 6:
            font_size = 20
        else:
            font_size = 16
            
        value_font = pygame.font.SysFont("Clear Sans", font_size, bold=True)
        text = value_font.render(value_str, True, text_color)
        text_rect = text.get_rect(center=(self.x + CELL_SIZE//2, self.y + CELL_SIZE//2))
        screen.blit(text, text_rect)
        
        # Add a star icon for target tiles
        if self.is_target_tile:
            # Draw a small star
            crown_text = value_font.render("★", True, (255, 255, 255))
            crown_rect = crown_text.get_rect(center=(self.x + CELL_SIZE//2, self.y + CELL_SIZE//4 - 10))
            screen.blit(crown_text, crown_rect)
            
        # Add a special indicator for special tiles (previous level targets)
        elif self.is_special:
            # Draw a small crown or other symbol
            special_text = value_font.render("♦", True, (255, 255, 255))
            special_rect = special_text.get_rect(center=(self.x + CELL_SIZE//2, self.y + CELL_SIZE//4 - 10))
            screen.blit(special_text, special_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tile Merger Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Clear Sans", 36, bold=True)
        self.ui_font = pygame.font.SysFont("Clear Sans", 24)
        self.title_font = pygame.font.SysFont("Clear Sans", 48, bold=True)
        
        self.state = STATE_PLAYING
        self.level = 1
        self.total_score = 0
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.tiles = []
        
        # Initialize with a power of 2 target
        self.current_target = 64  # Start with 64 as the first target
        self.targets = [self.current_target]  # Store all targets for reference
        
        self.selected_tile = None
        self.move_in_progress = False
        self.last_time = time.time()
        self.add_new_tile_after_move = False
        self.chain_merge_message = ""
        self.chain_merge_timer = 0
        
        # Timer variables
        self.level_start_time = time.time()  # When the current level started
        self.level_completion_time = 0       # How long it took to complete the level
        self.best_times = {}                 # Store best times for each level
        
        self.initialize_grid()

    def initialize_grid(self):
        """Initialize the grid with starting tiles (only used for first level)"""
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.tiles = []
        self.selected_tile = None
        self.add_new_tile_after_move = False
        
        # Reset the level timer
        self.level_start_time = time.time()
        self.level_completion_time = 0
        
        # Add 2 random tiles to start
        self.add_random_tile()
        self.add_random_tile()

    def add_random_tile(self):
        """Add a new tile to a random empty cell in the top row"""
        # Check if we need to ensure minimum empty spaces (at least 3)
        total_cells = GRID_SIZE * GRID_SIZE
        filled_cells = len(self.tiles)
        empty_cells_count = total_cells - filled_cells
        
        # If we have fewer than 3 empty cells, remove tiles until we have at least 3
        while empty_cells_count < 3:
            self.remove_low_value_tile()
            filled_cells = len(self.tiles)
            empty_cells_count = total_cells - filled_cells
        
        # Find empty cells in the top row
        empty_top_cells = [(0, c) for c in range(GRID_SIZE) if self.grid[0][c] is None]
        
        # If top row is full, find any empty cell
        if not empty_top_cells:
            empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                          if self.grid[r][c] is None]
            if not empty_cells:
                return False  # No empty cells
            r, c = random.choice(empty_cells)
        else:
            r, c = random.choice(empty_top_cells)
        
        # Determine tile value - only basic values: 2 (70%), 4 (30%)
        # No special tiles in random generation
        value_options = [2, 2, 2, 2, 2, 2, 2, 4, 4, 4]
        value = random.choice(value_options)
        
        # Create the tile (never special from random generation)
        self.grid[r][c] = Tile(value, r, c, is_special=False)
        new_tile = self.grid[r][c]
        self.tiles.append(new_tile)
        
        # Check if this tile matches or exceeds the target value
        if value >= self.current_target:
            new_tile.is_target_tile = True
            self.state = STATE_LEVEL_COMPLETE
            # Add the value to total score when target is reached
            self.total_score += value
            
        # Important: Do NOT check for chain merges here - let the user initiate merges
        
        return True

    def remove_low_value_tile(self):
        """Remove a random low-value tile to make space for new tiles"""
        if not self.tiles:
            return False
            
        # Sort tiles by value (lowest first)
        low_value_tiles = sorted(self.tiles, key=lambda t: t.value)
        
        # Take the lowest 25% of tiles
        num_candidates = max(1, len(low_value_tiles) // 4)
        candidates = low_value_tiles[:num_candidates]
        
        # Don't remove selected tiles or special/target tiles
        valid_candidates = [t for t in candidates if not (t.selected or t.is_special or t.is_target_tile)]
        
        if valid_candidates:
            # Remove a random low-value tile
            tile_to_remove = random.choice(valid_candidates)
            self.grid[tile_to_remove.row][tile_to_remove.col] = None
            self.tiles.remove(tile_to_remove)
            
            # If we removed the selected tile, clear the selection
            if tile_to_remove == self.selected_tile:
                self.selected_tile = None
                
            return True
            
        return False

    def check_for_merges(self, row, col):
        """DISABLED - No automatic merges allowed"""
        # This function is now disabled to prevent automatic tile value changes
        return False

    def check_for_chain_merges(self):
        """DISABLED - No automatic chain merges allowed"""
        # This function is now disabled to prevent automatic tile value changes
        return False

    def check_target_tiles(self):
        """Check for tiles that match or exceed the current target value"""
        for tile in self.tiles:
            # Mark tiles that match or exceed the current target
            tile.is_target_tile = (tile.value >= self.current_target)
            
            # If we find a target tile, the level is complete
            if tile.is_target_tile:
                self.state = STATE_LEVEL_COMPLETE

    def check_matching_tiles(self):
        """Check if there are any matching tiles on the board"""
        # Check for possible merges
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    value = self.grid[r][c].value
                    # Check adjacent cells for same value
                    for dr, dc in [(0,1), (1,0), (-1,0), (0,-1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                            if self.grid[nr][nc] and self.grid[nr][nc].value == value:
                                return True  # Found matching tiles
        return False  # No matching tiles found

    def check_low_tile_count(self):
        """Check if there are only two tiles of different values left and add more tiles if needed"""
        if len(self.tiles) == 2:
            # Check if the two tiles have different values
            if self.tiles[0].value != self.tiles[1].value:
                # Add exactly 1 random tile
                self.add_random_tile()
                return True
        return False

    def select_tile(self, row, col):
        """Select a tile at the given position"""
        if self.state != STATE_PLAYING or self.move_in_progress:
            return False
            
        # Deselect current tile if any
        if self.selected_tile:
            self.selected_tile.selected = False
            
        # If clicked on a tile, select it
        if self.grid[row][col]:
            self.selected_tile = self.grid[row][col]
            self.selected_tile.selected = True
            return True
        else:
            self.selected_tile = None
            return False

    def move_selected_tile(self, direction):
        """Move the selected tile in the specified direction"""
        if (self.state != STATE_PLAYING or self.move_in_progress or 
            not self.selected_tile):
            return False
            
        # Calculate target position
        row, col = self.selected_tile.row, self.selected_tile.col
        target_row, target_col = row, col
        
        if direction == "up":
            target_row = max(0, row - 1)
        elif direction == "down":
            target_row = min(GRID_SIZE - 1, row + 1)
        elif direction == "left":
            target_col = max(0, col - 1)
        elif direction == "right":
            target_col = min(GRID_SIZE - 1, col + 1)
            
        # Check if target position is valid (empty or same value)
        if target_row == row and target_col == col:
            return False  # No movement (at edge)
            
        if self.grid[target_row][target_col] is None:
            # Move to empty space
            self.grid[target_row][target_col] = self.selected_tile
            self.grid[row][col] = None
            
            # Set movement animation
            self.selected_tile.target_row = target_row
            self.selected_tile.target_col = target_col
            self.selected_tile.target_x = MARGIN + target_col * (CELL_SIZE + MARGIN)
            self.selected_tile.target_y = MARGIN + target_row * (CELL_SIZE + MARGIN)
            self.selected_tile.moving = True
            
            self.move_in_progress = True
            
            # Check for chain merges after move
            self.check_for_merges(target_row, target_col)
            
            # Add a new tile after every move
            self.add_new_tile_after_move = True
            
            return True
            
        elif self.grid[target_row][target_col].value == self.selected_tile.value:
            # Merge with same value
            target_tile = self.grid[target_row][target_col]
            new_value = self.selected_tile.value * 2
            
            # Update the target tile
            target_tile.value = new_value
            target_tile.merge_animation = 1
            
            # Special tiles are only added at level start, not created during gameplay
            target_tile.is_special = False
            
            # Check if the new value matches or exceeds the current target
            if new_value >= self.current_target:
                target_tile.is_target_tile = True
                self.state = STATE_LEVEL_COMPLETE
                # Add the value to total score only when target is reached
                self.total_score += new_value
            
            # Remove the selected tile
            self.grid[row][col] = None
            self.tiles.remove(self.selected_tile)
            self.selected_tile = None
            
            self.move_in_progress = True
            
            # No automatic chain merges - only user-initiated moves
            
            # Add a new tile after every move
            self.add_new_tile_after_move = True
            
            return True
            
        return False  # Invalid move

    def check_level_completion(self):
        """Check if any tile has reached or exceeded the target value"""
        for tile in self.tiles:
            if tile.value >= self.current_target:
                tile.is_target_tile = True
                self.state = STATE_LEVEL_COMPLETE
                
                # Record the completion time
                self.level_completion_time = time.time() - self.level_start_time
                
                # Check if this is a new best time
                if self.level not in self.best_times or self.level_completion_time < self.best_times[self.level]:
                    self.best_times[self.level] = self.level_completion_time
                
                # Add the value to total score when target is reached
                self.total_score += tile.value
                return True
        return False

    def check_game_over(self):
        """Check if the game is over (no valid moves left)"""
        # If there are empty cells, game is not over
        if any(any(cell is None for cell in row) for row in self.grid):
            return False
            
        # Check for possible merges
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = self.grid[r][c].value
                
                # Check adjacent cells for same value
                for dr, dc in [(0,1), (1,0), (-1,0), (0,-1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        if self.grid[nr][nc].value == value:
                            return False
        
        # No moves left
        return True

    def generate_achievable_target(self):
        """Generate a target that's a power of 2 and achievable with the current tiles"""
        # Get all tile values
        tile_values = [tile.value for tile in self.tiles]
        
        if not tile_values:
            # If no tiles, return a default target
            return 128
            
        # Find the highest tile value
        max_value = max(tile_values)
        
        # Find the next power of 2 that's higher than the current max value
        # This ensures the target is achievable by merging existing tiles
        next_power = 2
        while next_power <= max_value:
            next_power *= 2
            
        # Make sure the target is at least one power of 2 higher than the previous target
        min_target = self.current_target * 2
        
        # Choose the larger of the two options to ensure progression
        target = max(next_power, min_target)
            
        return target

    def advance_level(self):
        """Progress to next level while keeping ALL existing tiles"""
        # Increment level
        self.level += 1
        
        # Generate a new target that's a power of 2
        self.current_target = self.generate_achievable_target()
        self.targets.append(self.current_target)
        
        # Reset the level timer
        self.level_start_time = time.time()
        self.level_completion_time = 0
        
        # Reset game state variables but KEEP ALL TILES
        self.selected_tile = None
        self.move_in_progress = False
        self.add_new_tile_after_move = False  # Important: Don't trigger automatic merges
        self.chain_merge_message = ""
        self.chain_merge_timer = 0
        
        # Reset target tile flags
        for tile in self.tiles:
            tile.is_target_tile = (tile.value >= self.current_target)
            # If any tile already meets the new target, complete the level immediately
            if tile.is_target_tile:
                self.state = STATE_LEVEL_COMPLETE
                self.level_completion_time = 0  # Instant completion
                if self.level not in self.best_times or 0 < self.best_times[self.level]:
                    self.best_times[self.level] = 0
                self.total_score += tile.value
                return
        
        # If we have fewer than 2 tiles, add some new ones
        # This is just a safety measure in case the player has very few tiles left
        if len(self.tiles) < 2:
            # Find empty cells to add new tiles
            empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                          if self.grid[r][c] is None]
            
            # Add up to 2 new tiles if there's space
            for _ in range(min(2, len(empty_cells))):
                if empty_cells:
                    r, c = random.choice(empty_cells)
                    empty_cells.remove((r, c))
                    
                    # Create a new basic tile (2 or 4)
                    value = random.choice([2, 2, 2, 4])
                    self.grid[r][c] = Tile(value, r, c, is_special=False)
                    self.tiles.append(self.grid[r][c])
        
        # Important: Do NOT check for chain merges here - let the user initiate merges
        
        self.state = STATE_PLAYING
        
    def add_special_tile(self, value):
        """Add a special tile with the given value to the grid"""
        # Find an empty cell, preferably in the center area
        center_cells = [(r, c) for r in range(1, 3) for c in range(1, 3) 
                       if self.grid[r][c] is None]
        
        if center_cells:
            r, c = random.choice(center_cells)
        else:
            # If center is full, find any empty cell
            empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                          if self.grid[r][c] is None]
            if not empty_cells:
                return False  # No empty cells
            r, c = random.choice(empty_cells)
        
        # Create the special tile
        self.grid[r][c] = Tile(value, r, c, is_special=True)
        new_tile = self.grid[r][c]
        self.tiles.append(new_tile)
        
        return True

    def draw(self):
        """Draw the game state"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw grid background
        pygame.draw.rect(self.screen, GRID_COLOR,
                        (0, 0, WINDOW_WIDTH, GRID_SIZE*(CELL_SIZE+MARGIN)+MARGIN))
        
        # Draw empty cells
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                pygame.draw.rect(self.screen, EMPTY_CELL_COLOR,
                               (MARGIN + c*(CELL_SIZE+MARGIN),
                                MARGIN + r*(CELL_SIZE+MARGIN),
                                CELL_SIZE, CELL_SIZE), 0, 5)
        
        # Draw tiles
        for tile in self.tiles:
            tile.draw(self.screen, self.font)
        
        # Draw UI
        self.draw_ui()
        pygame.display.flip()

    def format_time(self, seconds):
        """Format time in seconds to HH:MM:SS format"""
        # Calculate hours, minutes, and seconds
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_part = int(seconds % 60)
        
        # Format as HH:MM:SS
        return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"

    def draw_ui(self):
        """Draw user interface elements"""
        y_offset = GRID_SIZE*(CELL_SIZE+MARGIN) + 20
        
        # Use consistent font for all main UI elements
        ui_title_font = pygame.font.SysFont("Clear Sans", 36, bold=True)
        
        # Increase spacing between elements
        spacing = 60  # Increased from 40 to 60 for more separation
        
        # Put LEVEL and TARGET on the same line
        # For unlimited levels, ensure the level number is displayed properly
        level_text = ui_title_font.render(f"LEVEL {self.level}", True, TEXT_COLOR)
        target_text = ui_title_font.render(f"TARGET {self.current_target}", True, TARGET_TILE_COLOR)
        
        # Calculate positions to place them on the same line with space between
        total_width = level_text.get_width() + target_text.get_width() + 80  # 80px space between
        level_x = (WINDOW_WIDTH - total_width) // 2
        target_x = level_x + level_text.get_width() + 80
        
        # Draw LEVEL and TARGET on the same line
        self.screen.blit(level_text, (level_x, y_offset))
        self.screen.blit(target_text, (target_x, y_offset))
        
        # Display timer with clock icon below with increased spacing
        if self.state == STATE_PLAYING:
            current_time = time.time() - self.level_start_time
            time_str = self.format_time(current_time)
        else:
            time_str = self.format_time(self.level_completion_time)
        
        # Create a small clock icon using text (Unicode clock symbol)
        clock_icon = ui_title_font.render("🕒", True, (0, 100, 200))
        time_text = ui_title_font.render(f" {time_str}", True, (0, 100, 200))
        
        # Calculate positions to center the clock icon and time text together
        icon_and_time_width = clock_icon.get_width() + time_text.get_width()
        clock_x = (WINDOW_WIDTH - icon_and_time_width) // 2
        time_x = clock_x + clock_icon.get_width()
        
        # Draw clock icon and time text centered below LEVEL and TARGET with more space
        self.screen.blit(clock_icon, (clock_x, y_offset + spacing))
        self.screen.blit(time_text, (time_x, y_offset + spacing))
        
        # Display best time if available
        if self.level in self.best_times:
            best_time = self.best_times[self.level]
            best_time_text = self.ui_font.render(f"BEST TIME: {self.format_time(best_time)}", True, (0, 150, 0))
            self.screen.blit(best_time_text, (WINDOW_WIDTH//2 - best_time_text.get_width()//2, y_offset + spacing * 2))
        
        # Display chain merge message if active
        if self.chain_merge_timer > 0:
            message_text = self.ui_font.render(self.chain_merge_message, True, (255, 100, 100))
            # Position below other UI elements
            message_y = y_offset + spacing * (3 if self.level in self.best_times else 2)
            self.screen.blit(message_text, (WINDOW_WIDTH//2 - message_text.get_width()//2, message_y))
        
        # Game state messages
        if self.state == STATE_LEVEL_COMPLETE:
            self.draw_message("Level Complete!", "")  # Empty subtitle, we handle it in draw_message
        elif self.state == STATE_GAME_OVER:
            self.draw_message("Game Over", f"Final Score: {self.total_score}")

    def draw_message(self, title, subtitle):
        """Draw a centered message box"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay, (0,0))
        
        # For level completion, show only "HURRAY!" and best time
        if title == "Level Complete!":
            # Use a larger, more celebratory font for HURRAY!
            hurray_font = pygame.font.SysFont("Clear Sans", 64, bold=True)
            hurray_text = hurray_font.render("HURRAY!", True, (255, 215, 0))  # Gold color
            
            # Show best time if available
            if self.level in self.best_times:
                best_time = self.best_times[self.level]
                best_time_text = self.font.render(f"BEST TIME: {self.format_time(best_time)}", True, WHITE)
            else:
                best_time_text = self.font.render(f"TIME: {self.format_time(self.level_completion_time)}", True, WHITE)
                
            # Add instruction to continue
            continue_text = self.ui_font.render("Press SPACE BAR to continue", True, WHITE)
            
            # Position all elements with proper spacing
            self.screen.blit(hurray_text, 
                           (WINDOW_WIDTH//2 - hurray_text.get_width()//2, 
                            WINDOW_HEIGHT//2 - 80))
            self.screen.blit(best_time_text,
                           (WINDOW_WIDTH//2 - best_time_text.get_width()//2,
                            WINDOW_HEIGHT//2))
            self.screen.blit(continue_text,
                           (WINDOW_WIDTH//2 - continue_text.get_width()//2,
                            WINDOW_HEIGHT//2 + 60))
        else:
            # For other messages (like game over), use the original format
            title_text = self.title_font.render(title, True, WHITE)
            sub_text = self.font.render(subtitle, True, WHITE)
            
            self.screen.blit(title_text, 
                           (WINDOW_WIDTH//2 - title_text.get_width()//2, 
                            WINDOW_HEIGHT//2 - 50))
            self.screen.blit(sub_text,
                           (WINDOW_WIDTH//2 - sub_text.get_width()//2,
                            WINDOW_HEIGHT//2 + 20))

    def run(self):
        """Main game loop"""
        running = True
        while running:
            # Cap the frame rate to 60 FPS
            self.clock.tick(60)
            
            dt = time.time() - self.last_time
            self.last_time = time.time()
            
            # Update all tiles
            all_stopped = True
            for tile in self.tiles:
                tile.update(dt)
                if tile.moving:
                    all_stopped = False
            
            # Update chain merge message timer
            if self.chain_merge_timer > 0:
                self.chain_merge_timer -= dt
            
            # If a move was in progress and all tiles have stopped moving
            if self.move_in_progress and all_stopped:
                self.move_in_progress = False
                
                # No automatic chain merges - only user-initiated moves
                
                # Check if any tile has reached or exceeded the target value
                self.check_level_completion()
                
                # Check if there are only two different tiles left
                if self.check_low_tile_count():
                    # Tiles were added, no need to add more
                    pass
                # Add exactly one new tile after every move
                elif self.add_new_tile_after_move:
                    # Always add exactly 1 tile
                    self.add_random_tile()
                    self.add_new_tile_after_move = False
                    
                    # Check again for level completion after adding a new tile
                    self.check_level_completion()
                
                # Check for game over
                if self.state == STATE_PLAYING and self.check_game_over():
                    self.state = STATE_GAME_OVER
            
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    # Get grid coordinates from mouse position
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Convert mouse position to grid coordinates
                    grid_x = (mouse_pos[0] - MARGIN) // (CELL_SIZE + MARGIN)
                    grid_y = (mouse_pos[1] - MARGIN) // (CELL_SIZE + MARGIN)
                    
                    # Check if click is within grid bounds
                    if (0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE and 
                        not self.move_in_progress):
                        self.select_tile(grid_y, grid_x)
                            
                elif event.type == KEYDOWN:
                    if self.state == STATE_LEVEL_COMPLETE and event.key == K_SPACE:
                        self.advance_level()
                    elif self.state == STATE_GAME_OVER and event.key == K_SPACE:
                        self.__init__()  # Restart game
                    elif self.state == STATE_PLAYING and not self.move_in_progress:
                        if event.key == K_UP:
                            self.move_selected_tile("up")
                        elif event.key == K_DOWN:
                            self.move_selected_tile("down")
                        elif event.key == K_LEFT:
                            self.move_selected_tile("left")
                        elif event.key == K_RIGHT:
                            self.move_selected_tile("right")
                        elif event.key == K_c:  # Check for chain merges manually
                            self.check_for_chain_merges()
                        elif event.key == K_r:  # Restart level
                            self.initialize_grid()
            
            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
