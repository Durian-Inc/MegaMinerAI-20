# This is where you build your AI for the Catastrophe game.

from joueur.base_ai import BaseAI
import math
import time


class AI(BaseAI):
    """ The basic AI functions that are the same between games. """

    def get_name(self):
        """ This is the name you send to the server so your AI will control
            the player named this string.

        Returns
            str: The name of your Player.
        """
        
        return "Durian"

    def start(self):
        """ This is called once the game starts and your AI knows its playerID
        and game. You can initialize your AI here.
        """
        for x in self.player.structures:
            if x.type == "shelter":
                self.home = x

        # find which missionary position is closer to start
        start_loc = (self.player.cat.tile.x, self.player.cat.tile.y)
        self.m_target = self.game.get_tile_at(0, 10)
        self.m2_target = self.game.get_tile_at(25, 10)
        if(self.distance(start_loc, (self.m_target.x, self.m_target.y)) >
           self.distance(start_loc, (25, 10))):
            self.m_target = self.game.get_tile_at(25, 7)
            self.m2_target = self.game.get_tile_at(0, 7)

    def game_updated(self):
        """ This is called every time the game's state updates, so if you are
            tracking anything you can update it here.
        """
        # set up and refresh lists
        self.foods, self.materials, self.unowned_humans = [], [], []
        self.bushes, self.material_structures = [], []
        for tile in self.game.tiles:
            if tile.food > 0:
                self.foods.append(tile)
            elif tile.materials > 0:
                self.materials.append(tile)
            elif tile.harvest_rate > 0:
                self.bushes.append(tile)
            elif (tile.structure is not None and
                  tile.structure.owner is None and
                  tile.structure.type != "road"):
                self.material_structures.append(tile)
        for unit in self.game.units:
            if unit.job.title == "fresh human" and unit.owner is None:
                self.unowned_humans.append(unit)

    def end(self, won, reason):
        """ This is called when the game ends, you can clean up your data and
            dump files here if need be.

        Args:
            won (bool): True means you won, False means you lost.
            reason (str): The human readable string explaining why you won or
            lost.
        """

    def run_turn(self):
        """ This is called every time it is this AI.player's turn.

        Returns:
            bool: Represents if you want to end your turn. True means end your
            turn, False means to keep your turn going and re-call this
            function.
        """
        if self.game.current_turn == 0 or self.game.current_turn == 1:
            # self.base_start()
            self.attack_start()
            
        # All turns except first
        # Gathering
        
        gatherers = self.get_unit_type(self.player.units, "gatherer")
        sorted_foods = {}
        count = 0
        for g in gatherers:
            if g.food:
                if self.move_to_target(g, self.home.tile):
                    g.drop(self.home.tile, "food", g.food)
                continue
            if g.energy < g.job.action_cost:
                g.rest()
            for f in self.bushes:
                sorted_foods[self.distance((g.tile.x, g.tile.y),
                                           (f.x, f.y))] = f
            sorted_foods_keys = sorted(sorted_foods.keys())
            while sorted_foods[sorted_foods_keys[count]].turns_to_harvest != 0:
                count += 1
            if self.move_to_target(g, sorted_foods[sorted_foods_keys[count]]):
                g.harvest(sorted_foods[sorted_foods_keys[count]])
            count += 1

        enemy = self.player.opponent
        soldiers = self.get_unit_type(self.player.units, "soldier")
        for s in soldiers:
            # optimize
            if self.move_to_target(s, enemy.cat.tile):
                s.attack(enemy.cat.tile)

        # Missionaries
        missionaries = self.get_unit_type(self.player.units, "missionary")
        # only one missionary
        if len(missionaries) == 1:
            m_1 = missionaries[0]  # the one and only
            if m_1.energy < m_1.job.action_cost:
                self.move_to_target(m_1, self.player.cat.tile)
                if m_1.tile.has_neighbor(self.player.cat.tile):
                    m_1.rest()
            else:
                if len(self.unowned_humans) > 0:
                    target_human = None
                    for human in self.unowned_humans:
                        if target_human is None:
                            target_human = human
                        if self.distance((m_1.tile.x, m_1.tile.y),
                                         (human.tile.x, human.tile.y)) < self.distance((m_1.tile.x, m_1.tile.y), (human.tile.x, human.tile.y)):
                            target_human = human

                    self.move_to_target(m_1, target_human.tile)
                    if m_1.tile.has_neighbor(target_human.tile):
                        m_1.convert(target_human.tile)
                    if m_1.energy < m_1.job.action_cost:
                        m_1.rest()
                else:
                    self.move_to_target(m_1, self.m_target)
                #sorted_foods[self.distance((g.movement_target.x,
                #                            g.movement_target.y), (f.x, f.y))] = (f.x, f.y)
                #print(sorted_foods)
                pass
        elif len(missionaries) > 1:
            m_1 = missionaries[0]  # first missionary
            if m_1.energy < m_1.job.action_cost:
                self.move_to_target(m_1, self.player.cat.tile)
                if m_1.tile.has_neighbor(self.player.cat.tile):
                    m_1.rest()
            else:
                if len(self.unowned_humans) > 0:
                    target_human = None
                    for human in self.unowned_humans:
                        if target_human is None:
                            target_human = human
                        if self.distance((m_1.tile.x, m_1.tile.y),
                                         (human.tile.x, human.tile.y)) < self.distance((m_1.tile.x, m_1.tile.y), (human.tile.x, human.tile.y)):
                            target_human = human

                    self.move_to_target(m_1, target_human.tile)
                    if m_1.tile.has_neighbor(target_human.tile):
                        m_1.convert(target_human.tile)
                    if m_1.energy < m_1.job.action_cost:
                        m_1.rest()
                else:
                    self.move_to_target(m_1, self.m_target)
            m_2 = missionaries[1]  # second missionary
            if m_2.energy < m_2.job.action_cost:
                self.move_to_target(m_2, self.player.cat.tile)
                if m_2.tile.has_neighbor(self.player.cat.tile):
                    m_2.rest()
            else:
                if len(self.unowned_humans) > 0:
                    target_human = None
                    for human in self.unowned_humans:
                        if target_human is None:
                            target_human = human
                        if self.distance((m_2.tile.x, m_2.tile.y),
                                         (human.tile.x, human.tile.y)) < self.distance((m_2.tile.x, m_2.tile.y), (human.tile.x, human.tile.y)):
                            target_human = human

                    self.move_to_target(m_2, target_human.tile)
                    if m_2.tile.has_neighbor(target_human.tile):
                        m_2.convert(target_human.tile)
                    if m_2.energy < m_2.job.action_cost:
                        m_2.rest()
                else:
                    self.move_to_target(m_2, self.m2_target)

        # New humans
        new_humans = self.get_unit_type(self.player.units, "fresh human")
        if len(new_humans) > 0:
            for human in new_humans:
                self.move_to_target(human, self.player.cat.tile)
                if human.tile.has_neighbor(self.player.cat.tile):
                    if len(missionaries) < 2:
                        human.change_job("missionary")
                    else:
                        human.change_job("soldier")

        enemy = None
        for person in self.game.players:
            if person != self.player:
                enemy = person
        for unit in self.game.units:
            if unit.owner == self.player:
                if unit.moves > 0 and unit != self.player.cat:
                    self.move_to_target(unit, enemy.cat.tile)

        return True

    def find_path(self, start, goal):
        """ A very basic path finding algorithm (Breadth First Search) that
            when given a starting Tile, will return a valid path to the goal
            Tile.
        Args:
            start (Tile): the starting Tile
            goal (Tile): the goal Tile
        Returns:
            list[Tile]: A list of Tiles representing the path, the the first
            element being a valid adjacent Tile to the start, and the last
            element being the goal.
        """

        if start == goal:
            # no need to make a path to here...
            return []

        # queue of the tiles that will have their neighbors searched for 'goal'
        fringe = []

        # How we got to each tile that went into the fringe.
        came_from = {}

        # Enqueue start as the first tile to have its neighbors searched.
        fringe.append(start)

        # keep exploring neighbors of neighbors... until there are no more.
        while len(fringe) > 0:
            # the tile we are currently exploring.
            inspect = fringe.pop(0)

            # cycle through the tile's neighbors.
            for neighbor in inspect.get_neighbors():
                # if we found the goal, we have the path!
                if neighbor == goal:
                    # Follow the path backward to the start from the goal and
                    # return it.
                    path = [goal]

                    # Starting at the tile we are currently at, insert them
                    # retracing our steps till we get to the starting tile
                    while inspect != start:
                        path.insert(0, inspect)
                        inspect = came_from[inspect.id]
                    return path
                # else we did not find the goal, so enqueue this tile's
                # neighbors to be inspected

                # if the tile exists, has not been explored or added to the
                # fringe yet, and it is pathable
                if (neighbor and 
                   neighbor.id not in came_from and
                   neighbor.is_pathable()):
                    # add it to the tiles to be explored and add where it came
                    # from for path reconstruction.
                    fringe.append(neighbor)
                    came_from[neighbor.id] = inspect

        # if you're here, that means that there was not a path to get to where
        # you want to go.
        #   in that case, we'll just return an empty path.
        return []

    # if you need additional functions for your AI you can add them here
    def get_unit_type(self, units, kind):
        specific = []
        for i in units:
            if i.job.title == kind:
                specific.append(i)
        return specific

    def distance(self, p0, p1):
        return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

    def move_to_target(self, unit, target):
        moves = self.find_path(unit.tile, target)
        num_moves = len(moves) if unit.moves > len(moves) else unit.moves
        for x in range(0, num_moves):
            unit.move(moves[x])
            if unit.tile.has_neighbor(target):
                return True
        return False

    def base_start(self):
        gathercount = 0
        for i in self.player.units:
            if i != self.player.cat:
                if gathercount != 2:
                    i.change_job("gatherer")
                    gathercount += 1
                else:
                    i.change_job("missionary")

    def attack_start(self):
        for i in self.player.units:
            if i != self.player.cat:
                i.change_job("soldier")
