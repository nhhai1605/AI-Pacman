# secondTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).
import copy
import sys

from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'FlexibleAgent', second = 'FlexibleAgent', numTraining = 0):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class FlexibleAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).

        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)

        IMPORTANT: This method may run for at most 15 seconds.
        """

        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        CaptureAgent.registerInitialState(self, gameState)

        '''
        Your initialization code goes here, if you need any.
        '''
        self.initPos = gameState.getAgentPosition(self.index)
        self.height = gameState.data.layout.walls.height
        self.width = int(gameState.data.layout.walls.width / 2)
        self.borders = []
        self.beforeBorders = []
        self.borderX = 0
        self.beforeBorderX = 0
        if self.red:
            self.borderX = self.width - 1
            self.beforeBorderX = self.borderX - 2
        else:
            self.borderX = self.width
            self.beforeBorderX = self.borderX + 2
        for i in range(self.height):
            pos1 = (self.borderX, i)
            pos2 = (self.beforeBorderX, i)
            if not gameState.hasWall(pos1[0], pos1[1]):
                self.borders.append(pos1)
            if not gameState.hasWall(pos2[0], pos2[1]):
                self.beforeBorders.append(pos2)

        self.detectDistance = 5
        self.isOffensive = self.index == 0 or self.index == 1
        # self.isOffensive = False
        self.defendedFood = []
        self.partnerIndex = copy.deepcopy(self.getTeam(gameState))
        self.partnerIndex.remove(self.index)
        self.partnerIndex = self.partnerIndex[0]
        self.targetingFood = max([(self.getMazeDistance(self.initPos, capsule), capsule) for capsule in self.getCapsulesYouAreDefending(gameState)])[1] if self.getCapsulesYouAreDefending(gameState) else None
        self.isRetreating = False
        self.actionHistory = util.Queue()
        self.actionHistoryLimit = 10
        self.isLooping = False
        # self.isFirstDefender = not self.isOffensive
        self.isFirstDefender = self.index == 2 or self.index == 3
        self.initFood = copy.deepcopy(self.getFood(gameState).asList())
        self.hDict = {}
        self.retreatingDistance = 4
        self.isPatrolling = True
        self.foodLimit = 2
        self.enemyPacmanCurrentPosition = None

    def retrieveMazeDistance(self, pos1, pos2):
        distance = max(self.hDict.get((pos1, pos2), -1),
                        self.hDict.get((pos2, pos1), -1))
        if distance != -1:
            return distance
        distance = self.getMazeDistance(pos1, pos2)
        self.hDict[(pos1, pos2)] = distance
        return distance

    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        return successor

    def getEnemies(self, gameState):
        opponentIndices = self.getOpponents(gameState)
        enemies = [gameState.getAgentState(i) for i in opponentIndices]
        opponentInsightIndices = []
        for idx, e in enumerate(enemies):
            if e.getPosition() != None:
                opponentInsightIndices.append(opponentIndices[idx])
        return [(i, gameState.getAgentState(i)) for i in opponentInsightIndices]

    # def setAnotherFood(self, gameState, currentPosition):
    #     self.isRetreating = True
    #     maxFood = max([(self.retrieveMazeDistance(food, currentPosition), food) for food in self.getFood(gameState).asList()])[1]
    #     self.retreatingPoint = min([(self.retrieveMazeDistance(maxFood, border), border) for border in self.beforeBorders])[1]

    def chooseAction(self, gameState):
        import sys
        maxDepth = 2
        ourAgent = gameState.getAgentState(self.index)
        currPos = gameState.getAgentPosition(self.index)
        currFood = self.getFood(gameState).asList()
        previousState = self.getPreviousObservation()
        ourPrevAgent = ourAgent
        if previousState:
            ourPrevAgent = previousState.getAgentState(self.index)
        def loopCheck():
            # check if there are enough moves
            if len(self.actionHistory.list) == self.actionHistoryLimit:
                evenList = []
                oddList = []
                for i in range(self.actionHistoryLimit):
                    if i % 2 == 0:
                        evenList.append(self.actionHistory.list[i])
                    else:
                        oddList.append(self.actionHistory.list[i])
                if evenList != oddList:
                    evenResult = all(e == evenList[0] for e in evenList)
                    oddResult = all(e == oddList[0] for e in oddList)
                    if evenResult and oddResult:
                        self.isLooping = True
                    else:
                        self.isLooping = False

        # check if the agent has died/ at starting pos
        if currPos == self.initPos:
            self.isLooping = False
            self.actionHistory = util.Queue()
            self.isRetreating = False

        # Pacman is attacking but retreating to border
        if ourPrevAgent:
            if not ourAgent.isPacman and ourPrevAgent.isPacman and not self.isRetreating:
                self.isRetreating = True
                # self.setRetreatingPoint(ourAgent.getPosition())
                # self.setAnotherFood(gameState, ourAgent.getPosition())

        if self.isOffensive:
            loopCheck()
            if self.isLooping:
                self.isRetreating = True
                # self.setRetreatingPoint(ourAgent.getPosition())
                # self.setAnotherFood(gameState, ourAgent.getPosition())
                self.actionHistory = util.Queue()
                self.isLooping = False
            else:
                if self.isRetreating:
                    multiplier = 1 if self.red else -1
                    if currPos[0] == self.borderX - multiplier * self.retreatingDistance:
                        self.isRetreating = False

        if not self.isFirstDefender:
            if self.getScore(gameState) >= 6:
                self.isOffensive = False
            else:
                self.isOffensive = True
            self.isRetreating = False

        if len(currFood) <= self.foodLimit:
            self.isRetreating = True

        indices = [self.index]
        if self.isOffensive:
            opponentInsightIndices = [e[0] for e in self.getEnemies(gameState) if not e[1].isPacman and self.retrieveMazeDistance(ourAgent.getPosition(), e[1].getPosition()) <= self.detectDistance]
        else:
            opponentInsightIndices = [e[0] for e in self.getEnemies(gameState) if e[1].isPacman]

        if opponentInsightIndices:
            opponentIndex = min([(self.retrieveMazeDistance(gameState.getAgentPosition(idx), ourAgent.getPosition()), idx) for idx in opponentInsightIndices])[1]
            self.enemyPacmanCurrentPosition = gameState.getAgentPosition(opponentIndex)
            indices += [opponentIndex]

        def maxValue(currentGameState, arrayIndex, currentDepth):
            if currentDepth == maxDepth:
                return self.evaluateFunction(currentGameState), "Stop"
            valueMoveList = [(-sys.maxsize, "Stop")]
            for a in currentGameState.getLegalActions(indices[arrayIndex]):
                nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
                value2, a2 = expectValue(nextState, arrayIndex + 1, currentDepth)
                valueMoveList.append((value2, a))
            valueMoveList = [v for v in valueMoveList if v[1] != "Stop"]
            # print(valueMoveList)
            # print(max(valueMoveList))
            return max(valueMoveList)

        def expectValue(currentGameState, arrayIndex, currentDepth):
            if currentDepth == maxDepth:
                return self.evaluateFunction(currentGameState), "Stop"
            if arrayIndex >= len(indices):
                arrayIndex = 0
                return maxValue(currentGameState, arrayIndex, currentDepth + 1)
            value, move = 0, "Stop"
            actions = currentGameState.getLegalActions(indices[arrayIndex])
            for a in actions:
                nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
                value2, a2 = expectValue(nextState, arrayIndex + 1, currentDepth)
                value += value2
                move = a
            value /= len(actions)
            return value, move

        def expectimax(currentGameState, arrayIndex, depth):
            value, move = maxValue(currentGameState, arrayIndex, depth)
            return value, move

        action = expectimax(gameState, 0, 0)[1]

        if len(self.actionHistory.list) >= self.actionHistoryLimit:
            self.actionHistory.pop()
        self.actionHistory.push(action)
        # print("final action: " + str(action))
        return action


    def checkDeadEnd(self, gameState, position, checkAdj=False):
        x = int(position[0])
        y = int(position[1])
        if checkAdj:
            wallCount = 0
            nextPath = []
            if gameState.hasWall(x+1, y):
                wallCount += 1
            else:
                nextPath.append((x+1, y))
            if gameState.hasWall(x-1, y):
                wallCount += 1
            else:
                nextPath.append((x-1, y))
            if gameState.hasWall(x, y-1):
                wallCount += 1
            else:
                nextPath.append((x, y-1))
            if gameState.hasWall(x, y+1):
                wallCount += 1
            else:
                nextPath.append((x, y+1))
            if wallCount >= 3:
                return True
            else:
                for path in nextPath:
                    x = int(path[0])
                    y = int(path[1])
                    wallCount = 0
                    if gameState.hasWall(x + 1, y):
                        wallCount += 1
                    if gameState.hasWall(x - 1, y):
                        wallCount += 1
                    if gameState.hasWall(x, y - 1):
                        wallCount += 1
                    if gameState.hasWall(x, y + 1):
                        wallCount += 1
                    if wallCount >= 3:
                        # print("Dead end: (" + str(x) + "," + str(y) + ")")
                        return True
            return False
        else:
            wallCount = 0
            if gameState.hasWall(x+1, y):
                wallCount += 1
            if gameState.hasWall(x-1, y):
                wallCount += 1
            if gameState.hasWall(x, y-1):
                wallCount += 1
            if gameState.hasWall(x, y+1):
                wallCount += 1
            if wallCount >= 3:
                return True
            else:
                return False

    def isInDefendingZone(self, currPos):
        midHeight = self.height / 2
        if self.isFirstDefender:
            if currPos[1] >= midHeight:
                return False
        else:
            if currPos[1] < midHeight:
                return False
        return True



    def evaluateFunction(self, currentGameState):
        ourAgent = currentGameState.getAgentState(self.index)
        currPos = currentGameState.getAgentPosition(self.index)
        score = 0
        otherAgentPos = currentGameState.getAgentPosition(self.partnerIndex)
        currCapsules = self.getCapsules(currentGameState)
        previousState = self.getPreviousObservation()
        ourPrevAgent = ourAgent
        closestBorderDistance, closestBorder = min([(self.retrieveMazeDistance(currPos, border), border) for border in self.borders])

        if previousState:
            prevDefendingFood = self.getFoodYouAreDefending(previousState).asList()
            ourPrevAgent = previousState.getAgentState(self.index)
        else:
            prevDefendingFood = []

        if currPos == self.initPos:
            return -sys.maxsize

        if self.isOffensive:
            currGhostStates = [e[1] for e in self.getEnemies(currentGameState) if not e[1].isPacman and self.retrieveMazeDistance(ourAgent.getPosition(), e[1].getPosition()) <= self.detectDistance]
            currScaredTimes = [ghostState.scaredTimer for ghostState in currGhostStates]
            currGhostStates = [ghostState.getPosition() for ghostState in currGhostStates]
            currFood = self.getFood(currentGameState).asList()
            closestCapsuleDistance, closestCapsule = min([(self.retrieveMazeDistance(currPos, capsule), capsule) for capsule in currCapsules]) if currCapsules else (0, [])
            closestFoodDistance, closestFood = min([(self.retrieveMazeDistance(currPos, food), food) for food in currFood]) if currFood else (0, [])

            def getFindingFoodEval():
                evalScore = 0
                evalScore -= closestCapsuleDistance
                evalScore -= 500 * len(currCapsules)
                evalScore -= closestFoodDistance
                evalScore -= 1000 * len(currFood)
                return evalScore

            def getRetreatingEval():
                if self.isRetreating:
                    # evalScore = -100 * self.retrieveMazeDistance(currPos, self.initPos)
                    evalScore = -100 * self.retrieveMazeDistance(currPos, self.initPos)
                    return evalScore
                else:
                    return None


            if closestFoodDistance > closestBorderDistance and ourPrevAgent.numCarrying >= 5:
                self.isRetreating = True

            retreatingScore = getRetreatingEval()
            if retreatingScore:
                score = retreatingScore
            else:
                ghostNearby = False
                closestGhostDistance = 1
                closestGhost = None
                if len(currGhostStates) > 0:
                    closestGhostDistance, closestGhost = min([(self.retrieveMazeDistance(currPos, ghostState), ghostState) for ghostState in currGhostStates])
                    if currScaredTimes[currGhostStates.index(closestGhost)] <= 10:
                        ghostNearby = True
                if ghostNearby and ourAgent.isPacman:
                    score -= sys.maxsize / closestGhostDistance
                    if closestCapsuleDistance < closestBorderDistance:
                        score -= closestCapsuleDistance
                    else:
                        score -= closestBorderDistance
                    if self.checkDeadEnd(currentGameState, ourAgent.getPosition()):
                        score -= sys.maxsize
                else:
                    score += getFindingFoodEval()

        else:
            currDefendingFood = self.getFoodYouAreDefending(currentGameState).asList()
            if self.targetingFood is None:
                if self.isFirstDefender:
                    furthestDistance, self.targetingFood = max([(self.retrieveMazeDistance(self.initPos, food), food) for food in currDefendingFood]) if currDefendingFood else (0, None)
                else:
                    furthestDistance, self.targetingFood = min([(self.retrieveMazeDistance(self.initPos, food), food) for food in currDefendingFood]) if currDefendingFood else (0, None)

            # get food that the defensive ghost will target
            def getTargetingFoodDist():
                if currDefendingFood:
                    if self.targetingFood == currPos:
                        self.isPatrolling = True
                    # if the previous food is not the same as current
                    if prevDefendingFood != currDefendingFood:
                        # pacman will go to the food that has been eaten
                        lostFoods = list(set(prevDefendingFood).difference(currDefendingFood))
                        if lostFoods:
                            closestLostFood = min([(self.retrieveMazeDistance(currPos, food), food) for food in lostFoods])[1]
                            closestNextFoodDistance, closestNextFood = min([(self.retrieveMazeDistance(food, closestLostFood), food) for food in currDefendingFood])
                            if self.isPatrolling:
                                self.targetingFood = closestNextFood
                            else:
                                if self.retrieveMazeDistance(closestNextFood, currPos) < self.retrieveMazeDistance(self.targetingFood, currPos):
                                    self.targetingFood = closestNextFood
                    if self.isPatrolling:
                        # check if the ghost has reached targeting food
                        if self.targetingFood == currPos:
                            # add targeted food to list of food defended
                            self.defendedFood.append(self.targetingFood)
                            # update the list of food based on difference of the current food and the defended food
                            nextFood = list(set(copy.deepcopy(currDefendingFood)).difference(self.defendedFood))
                            # if we reached all the food, we need reset the route
                            if not nextFood:
                                self.defendedFood = []
                                nextFood = copy.deepcopy(currDefendingFood)
                            # if there are two ghosts defending
                            if self.isFirstDefender:
                                # the second ghost will take an opposite route compared to the first
                                distance, self.targetingFood = max([(self.retrieveMazeDistance(self.initPos, food), food) for food in nextFood])

                            else:
                                distance, self.targetingFood = min([(self.retrieveMazeDistance(self.initPos, food), food) for food in nextFood])
                    return self.retrieveMazeDistance(currPos, self.targetingFood)
                return 0

            currEnemyPacmanStates = [e[1] for e in self.getEnemies(currentGameState) if e[1].isPacman]
            currEnemyPacmanIndices = [e[0] for e in self.getEnemies(currentGameState) if e[1].isPacman]
            if ourAgent.isPacman:
                score -= sys.maxsize
            # if there is an enemy nearby
            if len(currEnemyPacmanStates) > 0:
                self.isPatrolling = True  # True but actually doesnt patrol but chase the pacman instead, but after chasing, it will continue patrolling
                # the first defender should always chase the pacman
                # the second will patrol the foods until there is the second pacman
                if self.isFirstDefender:
                    # targetPacmanDistance, targetPacmanIdx = min([(self.retrieveMazeDistance(currPos, pacmanState.getPosition()), pacmanState.getPosition()) for pacmanState in currEnemyPacmanStates])
                    targetPacmanDistance, targetPacmanIdx = min([(self.retrieveMazeDistance(currPos, currentGameState.getAgentPosition(idx)), idx) for idx in currEnemyPacmanIndices])
                else:
                    # targetPacmanDistance, targetPacman = max([(self.retrieveMazeDistance(otherAgentPos, pacmanState.getPosition()), pacmanState.getPosition()) for pacmanState in currEnemyPacmanStates])
                    targetPacmanDistance, targetPacmanIdx = min([(self.retrieveMazeDistance(currPos, currentGameState.getAgentPosition(idx)), idx) for idx in currEnemyPacmanIndices])
                    # should be the same target with other:
                    lastPacmanPos = None
                    currPacmanPos = self.enemyPacmanCurrentPosition
                    if previousState:
                        prevPacmanState = previousState.getAgentState(targetPacmanIdx)
                        if prevPacmanState:
                            lastPacmanPos = prevPacmanState.getPosition()
                    if lastPacmanPos:
                        predictRange = 8
                        x = int(currPacmanPos[0] - lastPacmanPos[0])
                        y = int(currPacmanPos[1] - lastPacmanPos[1])
                        # print("last: " + str(lastPacmanPos))
                        # print("curr: " + str(currPacmanPos))
                        # print("x,y" + str((x,y)))

                        predictPos = (currPacmanPos[0] + x * predictRange, currPacmanPos[1] + y * predictRange)
                        # print("first predict: " + str(predictPos))
                        if predictPos[0] < 0:
                            predictPos = (0, predictPos[1])
                        elif predictPos[0] >= self.width:
                            predictPos = (self.width - 1, predictPos[1])
                        # print("middle predict: " + str(predictPos))
                        if predictPos[1] < 0:
                            predictPos = (predictPos[0], 0)
                        elif predictPos[1] >= self.height:
                            predictPos = (predictPos[0], self.height - 1)
                        # print("second predict: " + str(predictPos))
                        while currentGameState.hasWall(predictPos[0], predictPos[1]):
                            newX = predictPos[0] - 1 * x
                            newY = predictPos[1] - 1 * y
                            predictPos = (newX, newY)
                        # print("last predict: " + str(predictPos))
                        targetPacmanDistance = self.retrieveMazeDistance(currPos, predictPos)
                        # except:
                        #     pass

                # if we are not scared
                if ourAgent.scaredTimer == 0:
                    # go eat the pacman
                    score -= 1000 * targetPacmanDistance
                # if we are scared
                else:
                    # run away from pacman but keep some distance
                    if targetPacmanDistance == 1:
                        score += 1000
                    else:
                        score -= 1000
                score -= 10000 * len(currEnemyPacmanStates)
            else:  # If doesn't detect any enemies, just patrolling around the foods
                score -= getTargetingFoodDist()





        return score



