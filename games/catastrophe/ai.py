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
        self.food_quota = 250

        for x in self.player.structures:
            if x.type == "shelter":
                self.home = x.tile

        # find which missionary position is closer to start
        start_loc = (self.player.cat.tile.x, self.player.cat.tile.y)
        x, y, o_x = None, None, None
        if start_loc[0] <= 7:
            y = 7
        else:
            y = 10
        if start_loc[1] <= 12:
            x, o_x = 0, 25
        else:
            x, o_x = 25, 0
        self.m_target = [self.game.get_tile_at(x, y),
                         self.game.get_tile_at(o_x, y)]

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
            self.base_start(len(self.bushes))
            # self.attack_start()

        if self.player.cat.energy < 100:
            self.player.cat.rest()

        builders = self.get_unit_type(self.player.units, "builder")
        # All turns except first
        # Gatherers
        gatherers = self.get_unit_type(self.player.units, "gatherer")
        sorted_foods = {}
        count = 0
        for g in gatherers:
            if g.food:
                if self.move_to_target(g, self.home):
                    g.drop(self.home, "food", g.food)
            elif g.energy < g.job.action_cost:
                if self.move_to_target(g, self.home):
                    g.rest()
            # elif self.player.food >= self.food_quota:
            #     if self.move_to_target(g, self.home):
            #         g.change_job("builder")
            else:
                for f in self.bushes:
                    sorted_foods[self.distance((g.tile.x, g.tile.y),
                                               (f.x, f.y))] = f
                sorted_foods_keys = sorted(sorted_foods.keys())
                while sorted_foods[sorted_foods_keys[count]].turns_to_harvest != 0 and count < len(sorted_foods_keys):
                    count += 1
                if self.move_to_target(g, sorted_foods[sorted_foods_keys[count]]):
                    g.harvest(sorted_foods[sorted_foods_keys[count]])
                count += 1

        # Soldiers
        enemy = self.player.opponent
        soldiers = self.get_unit_type(self.player.units, "soldier")
        try:
            if soldiers[0]:
                if soldiers[0].energy <= 30 and self.home is not None:
                    if self.move_to_target(soldiers[0], self.home):
                        soldiers[0].rest()
            else:
                # defend
                if self.in_range(self.player.cat) > 0:
                    if self.move_to_target(soldiers[0], self.player.cat.tile):
                        self.target_close(soldiers[0])
                elif self.in_range(soldiers[0]) > 0 and self.dist2(soldiers[0], enemy.cat) >= 3:
                    self.target_close(soldiers[0])
            if soldiers[1]:
                if soldiers[1].energy <= 30 and self.home is not None:
                    if self.move_to_target(soldiers[1], self.home):
                        soldiers[1].rest()
            else:
                # defend
                if self.in_range(self.player.cat) > 0:
                    if self.move_to_target(soldiers[1], self.player.cat.tile):
                        self.target_close(soldiers[1])
                elif self.in_range(soldiers[1]) > 0 and self.dist2(soldiers[1], enemy.cat) >= 3:
                    self.target_close(soldiers[1])
        except IndexError:
            pass

        for s in soldiers[2:]:
            if s.energy <= 30 and self.home is not None:
                if self.move_to_target(s, self.home):
                    s.rest()
            else:
                # defend
                if self.in_range(self.player.cat) > 0:
                    if self.move_to_target(s, self.player.cat.tile):
                        self.target_close(s)
                elif self.in_range(s) > 0 and self.dist2(s, enemy.cat) >= 3:
                    self.target_close(s)
                # attack
                else:
                    if self.move_to_target(s, enemy.cat.tile):
                        s.attack(enemy.cat.tile)

        # Missionaries
        missionaries = self.get_unit_type(self.player.units, "missionary")

        # no missionaries, this is bad
        if len(missionaries) < 1:
            closest_unit = None
            # search for closest builder
            for builder in builders:
                if closest_unit is None:
                    closest_unit = builder
                if self.dist2(closest_unit, self.player.cat) > self.dist2(
                    builder, self.player.cat
                ):
                    closest_unit = builder
            # we have no builders
            if closest_unit is None:
                # search for closest soldier
                for soldier in soldiers:
                    if closest_unit is None:
                        closest_unit = soldier
                    if self.dist2(closest_unit, self.player.cat) > self.dist2(
                        soldier, self.player.cat
                    ):
                        closest_unit = soldier
                # we have no soldiers
                if closest_unit is None:
                    # find closest unit
                    for unit in self.player.units:
                        if closest_unit is None:
                            closest_unit = unit
                        if self.dist2(closest_unit,
                                      self.player.cat) > self.dist2(
                                          unit, self.player.cat
                                      ):
                            closest_unit = unit
            # move the unit to the cat
            self.move_to_target(closest_unit, self.player.cat.tile)
            if closest_unit.tile.has_neighbor(self.player.cat.tile):
                # get full energy
                if closest_unit.energy < 100:
                    closest_unit.rest()
                else:
                    # become missionary
                    closest_unit.change_job("missionary")
        else:
            # we have at least one missionary
            for missionary in missionaries:
                other = None  # other missionary; if None, we only have one
                # find other missionary
                for m_2 in missionaries:
                    if m_2 is not missionary:
                        other = m_2
                # check energy
                if missionary.energy < missionary.job.action_cost:
                    # go to cat and rest
                    if self.move_to_target(missionary, self.player.cat.tile):
                        missionary.rest()
                else:
                    # we have enough energy, search for humans
                    if len(self.unowned_humans) > 0:
                        target_human = None  # human to chase
                        # find closest human not closer to other missionary
                        for human in self.unowned_humans:
                            # first human, gets the distance comparing started
                            if target_human is None:
                                target_human = human
                            # see if human is closer than target_human
                            if self.dist2(missionary,
                                          human) < self.dist2(missionary,
                                                              human):
                                target_human = human
                            # see if there's a second missionary
                            if other is not None:
                                # see if human is closer to other missionary
                                if self.dist2(missionary,
                                              human) > self.dist2(other,
                                                                  human):
                                    target_human = None
                        # see if we still have a human to chase
                        if target_human is not None:
                            # chase the human
                            if self.move_to_target(missionary,
                                                   target_human.tile):
                                # we have found the human, convert it
                                missionary.convert(target_human.tile)
                            # we converted a human but can still move
                            if missionary.energy < missionary.job.action_cost:
                                # go to the cat
                                if self.move_to_target(missionary,
                                                       self.player.cat.tile):
                                    # got to the cat, rest
                                    missionary.rest()
                        else:
                            # no human to chase, go to target
                            self.move_to_target(
                                missionary,
                                self.m_target[0]
                                if missionary is missionaries[0]
                                else self.m_target[1]
                            )
                    else:
                        # no humans on map, go to target
                        self.move_to_target(
                            missionary,
                            self.m_target[0]
                            if missionary is missionaries[0]
                            else self.m_target[1]
                        )

        # New humans
        # builder_quota = 0
        new_humans = self.get_unit_type(self.player.units, "fresh human")
        if len(new_humans) > 0:
            for human in new_humans:
                if self.move_to_target(human, self.player.cat.tile):
                    if len(missionaries) < 2:
                        human.change_job("missionary")
                    # elif len(self.get_unit_type(self.player.units, "builder")) != builder_quota:
                    #     human.change_job("builder")
                    else:
                        human.change_job("soldier")

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

    def dist2(self, obj1, obj2):
        return self.distance((obj1.tile.x, obj1.tile.y),
                             (obj2.tile.x, obj2.tile.y))

    def move_to_area(self, unit, target):
        moves = self.find_path(unit.tile, target)
        num_moves = len(moves) if unit.moves > len(moves) else unit.moves
        for x in range(0, num_moves):
            if moves[x] in unit.tile.get_neighbors() and not moves[x].unit:
                unit.move(moves[x])
            if unit.tile.has_neighbor(target):
                return True
        return False




    def path_to_area(self, unit, area):
        path = self.find_path(unit.tile, area)
        if path == []:
            for i in area.get_neighbors():
                path = self.path_to_area(unit, i)
                if path != []:
                    return path
        else:
            return path

    def move_to_target(self, unit, target):
        moves = self.path_to_area(unit, target)
        num_moves = len(moves) if unit.moves > len(moves) else unit.moves
        for x in range(0, num_moves):
            if moves[x] in unit.tile.get_neighbors() and not moves[x].unit:
                unit.move(moves[x])
            if unit.tile.has_neighbor(target):
                return True
        return False





    def base_start(self, num_bushes):
        gather_quota = 1
        gathercount = 0
        for i in self.player.units:
            if i != self.player.cat:
                if gathercount != gather_quota:
                    i.change_job("gatherer")
                    gathercount += 1
                else:
                    i.change_job("missionary")

    def attack_start(self):
        for i in self.player.units:
            if i != self.player.cat:
                i.change_job("soldier")

    def in_range(self, unit):
        squares = set()
        enemies = 0
        for x in unit.tile.get_neighbors():
            squares.add(x)
            for y in x.get_neighbors():
                squares.add(y)
                for z in y.get_neighbors():
                    squares.add(z)
        for i in squares:
            if i.unit and i.unit.owner != self.player:
                enemies += 1
        return enemies

    def target_close(self, fighter):
        squares = set()
        enemies = set()
        sorted_enemies = {}
        for x in fighter.tile.get_neighbors():
            squares.add(x)
            for y in x.get_neighbors():
                squares.add(y)
                for z in y.get_neighbors():
                    squares.add(z)

        for i in squares:
            if i.unit and i.unit.owner != self.player:
                    enemies.add(i.unit)

        for i in enemies:
            sorted_enemies[self.distance((i.tile.x, i.tile.y),
                                         (fighter.tile.x, fighter.tile.y))] = i

        sorted_enemies_keys = sorted(sorted_enemies.keys())
        if sorted_enemies_keys:
            if self.move_to_target(fighter, sorted_enemies[sorted_enemies_keys[0]].tile):
                fighter.attack(sorted_enemies[sorted_enemies_keys[0]].tile)
