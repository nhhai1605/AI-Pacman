# myTeam.py
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
import math
import sys
from game import Actions
from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'FlexibleAgentOne', second = 'FlexibleAgentTwo', numTraining = 0):
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

class FlexibleAgentOne(CaptureAgent):

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
        print("Final Submission version 1.0.1")
        self.initPos = gameState.getAgentPosition(self.index)
        self.height = gameState.data.layout.walls.height
        self.width = int(gameState.data.layout.walls.width / 2)
        self.borders = []
        self.enemyBorders = []
        self.borderX = 0
        self.enemyBorderX = 0
        if self.red:
            self.borderX = self.width - 1
            self.enemyBorderX = self.borderX + 1
        else:
            self.borderX = self.width
            self.enemyBorderX = self.borderX - 1
        for i in range(self.height):
            pos1 = (self.borderX, i)
            if not gameState.hasWall(pos1[0], pos1[1]):
                self.borders.append(pos1)
            pos2 = (self.enemyBorderX, i)
            if not gameState.hasWall(pos2[0], pos2[1]):
                self.enemyBorders.append(pos2)
        self.detectDistance = 6
        self.isOffensive = True
        self.isRetreating = False
        self.isFirstDefender = False
        self.initFood = copy.deepcopy(self.getFood(gameState).asList())
        self.hDict = {}
        self.foodLimit = 2
        self.lastGhostSeen = {}
        self.scaredTimerLimit = 3
        self.ghostNearby = False
        self.maxFoodCarryLimitNearGhost = 1
        self.maxFoodCarryLimitNearBorder = 3
        if self.initFood:
            self.scoreToChangeToDefender = math.floor((len(self.initFood) - 2) / 3)
        else:
            self.scoreToChangeToDefender = 0
        self.actionHistoryLimit = 10
        self.actionHistory = util.Queue()
        self.positionHistory = util.Queue()
        self.positionHistoryLimit = 10
        self.isLooping = False
        self.isStopping = False
        self.isStuck = False
        self.isAttacking = False
        self.retreatingDistance = 5
        self.pacmanNearby = False
        self.defendingBorder = None
        self.visitedBorders = []
        self.isPatrolling = True
        self.lastGhostSeenTimer = 15
        # see as wall parameters
        self.seeEnemyBorderAsWall = False
        self.isGoingForSafeFoodOnly = False
        self.seeFriendAsWall = False

        self.partnerIndex = copy.deepcopy(self.getTeam(gameState))
        self.partnerIndex.remove(self.index)
        self.partnerIndex = self.partnerIndex[0]

    # check if the agent is looping
    def loopCheck(self):
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
                # if the moves are the same
                if evenResult and oddResult:
                    self.isLooping = True
                else:
                    self.isLooping = False

    # check if the agent is stuck
    def stuckCheck(self):
        # check that the pacman is in attacking mode
        if self.isAttacking:
            # check if there are enough moves made
            if len(self.positionHistory.list) == self.positionHistoryLimit:
                count = 0
                # loop through the previous positions
                for pos in self.positionHistory.list:
                    # check if the pacman is in our territory
                    if pos[0] <= self.borderX:
                        count += 1
                 # check if the pacman is stuck looping in our territory
                if count >= 5:
                    # pacman is stuck
                    self.isStuck = True
                else:
                    # pacman is not stuck
                    self.isStuck = False

    # check if the agent has stopped moving
    def stopCheck(self):
        flag = True
        if len(self.actionHistory.list) == self.actionHistoryLimit:
            for a in self.actionHistory.list:
                if a != "Stop":
                    flag = False
        else:
            flag = False
        self.isStopping = flag

    # reset the states of the agent after it dies
    def resetState(self):
        self.actionHistory = util.Queue()
        self.positionHistory = util.Queue()
        self.isLooping = False
        self.isStopping = False
        self.isStuck = False

    def chooseAction(self, gameState):
        currAgent = gameState.getAgentState(self.index)
        currPos = gameState.getAgentPosition(self.index)
        currCapsules = self.getCapsules(gameState)
        enemyIndices, enemyStates = getEnemies(self, gameState)
        currFood = self.getFood(gameState).asList()
        timeLeft = gameState.data.timeleft
        timeEachMove = 4
        previousState = self.getPreviousObservation()
        prevAgent = currAgent
        if previousState:
            prevAgent = previousState.getAgentState(self.index)

        if currPos == self.initPos:
            self.resetState()
            self.isGoingForSafeFoodOnly = False
            self.lastGhostSeen = {}
            self.isAttacking = False
            self.isRetreating = False

        # check if our game score is high enough to switch to defender
        if self.getScore(gameState) >= self.scoreToChangeToDefender and not currAgent.isPacman:
            self.isOffensive = False
            self.seeEnemyBorderAsWall = True
        else:
            self.isOffensive = True
            self.seeEnemyBorderAsWall = False

        # if the agent is defensive, but it is scared, then changed back to offensive
        if currAgent.scaredTimer > 0:
            self.isOffensive = True
            self.seeEnemyBorderAsWall = False

        lastGhostSeenCounter(self)

        # if agent is offensive
        if self.isOffensive:
            # if there are only 2 food left
            if len(currFood) <= self.foodLimit:
                # agent goes to the border
                action = ucs(self, gameState, self.borders)[0]
                return action

            if currAgent.isPacman:
                self.isAttacking = True
            addPositionHistory(self, currPos)

            # check that the pacman is not looping/stuck or stopped
            if not self.isRetreating:
                self.loopCheck()
                self.stopCheck()
                self.stuckCheck()

            # these lines will determine when the agent finished its retreating.
            # For this agent, retreating will be go back to the initPos but when the there are some distance
            # between him and our border, then the retreating is complete.
            if self.isRetreating:
                distanceToClosestBorder = getClosestObject(self, currPos, self.borders)[0]
                if distanceToClosestBorder >= self.retreatingDistance:
                    if (self.red and currPos[0] <= self.borderX) or (not self.red and currPos[0] >= self.borderX):
                        self.isRetreating = False

            ghostList = []
            if enemyIndices:
                for idx in enemyIndices:
                    enemy = gameState.getAgentState(idx)
                    # Add last seen ghosts positions to a list
                    if enemy.scaredTimer < self.scaredTimerLimit and not enemy.isPacman:
                        # We will save the location of the enemy if the enemy is ghost and not scared
                        self.lastGhostSeen[idx] = (enemy.getPosition(), self.lastGhostSeenTimer)
                        # If the enemy is close, add it to the ghostList which will use for the decision later
                        if retrieveMazeDistance(self, currPos, enemy.getPosition()) <= self.detectDistance:
                            ghostList.append(enemy.getPosition())
                    else:
                        self.lastGhostSeen[idx] = None

            self.isGoingForSafeFoodOnly = False
            if ghostList:
                closestGhostDistance, closestGhost = getClosestObject(self, currPos, ghostList)
                # if there is a capsule(s) still on the map
                if currCapsules:
                    # calculating distance to capsule
                    distanceToCapsule, closestCapsule = min([(retrieveMazeDistance(self, currPos, capsule), capsule) for capsule in currCapsules])
                    # check how close the ghost is to the capsule
                    distanceFromGhostToCapsule = retrieveMazeDistance(self, closestCapsule, closestGhost)
                    # check if the agent can reach the capsule before the ghost, then go to the capsule
                    if distanceFromGhostToCapsule > distanceToCapsule:
                        return ucs(self, gameState, currCapsules)[0]
                # the pacman will retreat when it is carrying more than one food and there are no capsules on the map
                if currAgent.isPacman:
                    if currAgent.numCarrying >= self.maxFoodCarryLimitNearGhost:
                        self.isRetreating = True
                    else:
                        # if it is not carrying more than one food, it will not retreat and go for safe food
                        # safe food is food which is not in a dead end (3 walls adjacent), if all safe food are eaten,
                        # go for all food it can find.
                        if not areAllSafeFoodEaten(self, gameState):
                            self.isGoingForSafeFoodOnly = True


            # if agent is looping or stopped then retreat and reset the agent state
            if self.isLooping or self.isStopping:
                self.isRetreating = True
                self.resetState()

            # if there is a capsule and the agent is not retreating
            if currCapsules and not self.isRetreating:
                action = None
                # if the capsule is closer than the closest food
                if getClosestObject(self, currPos, currCapsules)[0] <= getClosestObject(self, currPos, currFood)[0]:
                    # go to capsule
                    action = ucs(self, gameState, currCapsules)[0]
                if action:
                    addActionHistory(self, action)
                    return action

            # If the agent is carrying the max food and is close to the border
            if (currAgent.numCarrying >= self.maxFoodCarryLimitNearBorder and \
               getClosestObject(self, currPos, self.borders)[0] <= getClosestObject(self, currPos, currFood)[0]) or currAgent.numCarrying >= self.maxFoodCarryLimitNearBorder * 3.5:
                # agent will retreat
                self.isRetreating = True

            # If time is running out then retreat
            if timeLeft <= (getClosestObject(self, currPos, self.borders)[0] + 2) * timeEachMove:
                self.isRetreating = True

            # agent retreats to the initial position
            if self.isRetreating:
                action = ucs(self, gameState, [self.initPos])[0]
                if action == "Stop":
                    action = ucs(self, gameState, self.borders)[0]
            else:
                if self.isGoingForSafeFoodOnly:
                    currFood = getSafeFood(self, gameState)
                if currAgent.scaredTimer > 0 and not currAgent.isPacman:
                    # astar to avoid the pacman when we are ghost and scared
                    action = astar(self, gameState, currFood)[0]
                else:
                    action = ucs(self, gameState, currFood)[0]

            addActionHistory(self, action)
            return action
        # if agent is defensive
        else:
            # agent will defend border
            if self.defendingBorder is None:
                self.defendingBorder = getClosestObject(self, currPos, self.borders)[1]
            else:
                pacmanStates = []
                if enemyStates:
                    for enemy in enemyStates:
                        if enemy.isPacman:
                            pacmanStates.append(enemy)
                # get the positions of enemy pacman seen in defensive half
                pacmanStates = [pacmanState.getPosition() for pacmanState in pacmanStates]
                self.seeFriendAsWall = False
                # if the agent detects enemy pacman, we will target the pacman
                if pacmanStates:
                    targetDistance, targetPacman = getClosestObject(self, currPos, pacmanStates)
                    distanceToPartner = retrieveMazeDistance(self, targetPacman, gameState.getAgentPosition(self.partnerIndex))
                    # However, if our partner are closer, then we will see our partner as a wall so that we can
                    # predict the path of the enemy pacman will go instead of just follow the pacman.
                    if distanceToPartner <= targetDistance:
                        self.seeFriendAsWall = True
                    return ucs(self, gameState, [targetPacman])[0]
                else:
                    # if there are no enemy pacman nearby, we will patrol at our border.
                    # These lines will update the border so that he will patrol thru every borders.
                    if currPos == self.defendingBorder:
                        self.visitedBorders.append(self.defendingBorder)
                        for border in self.borders:
                            if border not in self.visitedBorders:
                                if retrieveMazeDistance(self, border, self.defendingBorder) <= 3:
                                    self.visitedBorders.append(border)
                        nextBorders = list(set(copy.deepcopy(self.borders)).difference(self.visitedBorders))
                        if not nextBorders:
                            self.visitedBorders = []
                            nextBorders = copy.deepcopy(self.borders)
                        distance, self.defendingBorder = getClosestObject(self, currPos, nextBorders)
            return ucs(self, gameState, [self.defendingBorder])[0]


# This is our first attempt defensive agent using expectimax and evaluation function.
# However, we do not use this for our submission, so you don't need to worry or read this agent's code.
class DefensiveAgent(CaptureAgent):
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
        self.borderX = 0
        if self.red:
            self.borderX = self.width - 1
        else:
            self.borderX = self.width
        for i in range(self.height):
            pos1 = (self.borderX, i)
            if not gameState.hasWall(pos1[0], pos1[1]):
                self.borders.append(pos1)
        self.isFirstDefender = True
        self.initFood = copy.deepcopy(self.getFood(gameState).asList())
        self.hDict = {}
        self.maxDepth = 2
        self.targetingFood = None
        self.enemyPacmanCurrentPosition = None
        self.defendedFood = []
        self.isPatrolling = True
        self.isOffensive = True
        self.scoreLimit = 3
        self.isRetreating = False
        self.partnerIndex = copy.deepcopy(self.getTeam(gameState))
        self.partnerIndex.remove(self.index)
        self.partnerIndex = self.partnerIndex[0]
        self.detectDistance = 6
        self.scaredTimerLimit = 5
        self.maxFoodLimit = 3
        self.lastGhostSeen = {}
        self.seeFriendAsWall = False
        self.seeEnemyBorderAsWall = False
        self.isGoingForSafeFoodOnly= False

    # using expectimax technique for defensive agent
    def expectimax(self, gameState, maxDepth, indices):
        # get the max value
        def maxValue(currentGameState, currArrayIndex,  currentDepth):
            if currentDepth == maxDepth:
                return self.evaluateFunction(currentGameState), "Stop"
            valueMoveList = [(-sys.maxsize, "Stop")]
            actions = [s[1] for s in getSuccessorPosition(self, gameState, currentGameState.getAgentPosition(indices[currArrayIndex]))]
            for a in actions:
                nextState = currentGameState.generateSuccessor(indices[currArrayIndex], a)
                value2, a2 = expectValue(nextState, currArrayIndex + 1, currentDepth)
                valueMoveList.append((value2, a))
            valueMoveList = [v for v in valueMoveList if v[1] != "Stop"]
            return max(valueMoveList) if valueMoveList else (-sys.maxsize, "Stop")
        # get expected value
        def expectValue(currentGameState, currArrayIndex, currentDepth):
            if currentDepth == maxDepth:
                return self.evaluateFunction(currentGameState), "Stop"
            if currArrayIndex >= len(indices):
                arrayIndex = 0
                return maxValue(currentGameState, arrayIndex, currentDepth + 1)
            value, move = 0, "Stop"
            actions = currentGameState.getLegalActions(indices[currArrayIndex])
            for a in actions:
                nextState = currentGameState.generateSuccessor(indices[currArrayIndex], a)
                value2, a2 = expectValue(nextState, currArrayIndex + 1, currentDepth)
                value += value2
                move = a
            value /= len(actions)
            return value, move
        value, move = maxValue(gameState, 0, 0)
        return value, move

    def evaluateFunction(self, gameState):
        currAgent = gameState.getAgentState(self.index)
        currPos = gameState.getAgentPosition(self.index)
        currCapsules = self.getCapsulesYouAreDefending(gameState)
        currDefendingFood = self.getFoodYouAreDefending(gameState).asList()

        # previous state
        previousState = self.getPreviousObservation()
        prevAgent = currAgent
        if previousState:
            prevDefendingFood = self.getFoodYouAreDefending(previousState).asList()
            prevAgent = previousState.getAgentState(self.index)
        else:
            prevDefendingFood = []
        # if we are not scared
        score = 0
        # if agent is offensive
        if self.isOffensive:
            currEnemyGhostIndices, currEnemyGhostStates = [], []
            for idx in getEnemies(self, gameState)[0]:
                enemy = gameState.getAgentState(idx)
                if not enemy.isPacman and retrieveMazeDistance(self, currPos, enemy.getPosition()) <= self.detectDistance and enemy.scaredTimer <= self.scaredTimerLimit:
                    currEnemyGhostIndices.append(idx)
                    currEnemyGhostStates.append(enemy)
            currFood = self.getFood(gameState).asList()
            otherAgentPos = gameState.getAgentPosition(self.partnerIndex)

            if currCapsules:
                closestCapsuleDistance, closestCapsule = getClosestObject(self, currPos, currCapsules)
            else:
                closestCapsuleDistance, closestCapsule = 0, []
            closestBorderDistance, closestBorder = getClosestObject(self, currPos, self.borders)

            if currFood:
                (closestFoodDistance, closestFood) = getClosestObject(self, otherAgentPos, currFood)
                gotFood = False
                for food in currFood:
                    if abs(food[0] - closestFood[0]) <= 5 and abs(food[1] - closestFood[1]) >= 5:
                        closestFoodDistance, closestFood = retrieveMazeDistance(self, currPos, food), food
                        gotFood = True
                        break
                if not gotFood:
                    closestFoodDistance, closestFood = getClosestObject(self, currPos, currFood)
            else:
                self.isRetreating = True

            # finding evaluate score of food
            def getFindingFoodEval():
                evalScore = 0
                # evalScore -= closestCapsuleDistance
                # evalScore -= 500 * len(currCapsules)
                evalScore -= 10 * closestFoodDistance
                evalScore -= 1000 * len(currFood)
                return evalScore

            # evaluate the score by retrieveMazeDistance
            def getRetreatingEval():
                # check if the pacman is retreating
                if self.isRetreating:
                    # evalScore = -100 * retrieveMazeDistance(self, currPos, getClosestObject(self, currPos, self.borders)[1])
                    evalScore = -100 * retrieveMazeDistance(self, currPos, self.initPos)
                    return evalScore
                else:
                    return None
            # get the retreating score
            retreatingScore = getRetreatingEval()
            if retreatingScore:
                score = retreatingScore
            else:
                if len(currEnemyGhostStates) > 0:
                    ghostNearby = True
                    ghostPositions = [ghostState.getPosition() for ghostState in currEnemyGhostStates]
                    closestGhostDistance = getClosestObject(self,currPos, ghostPositions)[0]
                else:
                    ghostNearby = False
                    closestGhostDistance = 1
                # if ghost is very close and now agent is pacman
                if ghostNearby and currAgent.isPacman:
                    # get the score
                    score -= sys.maxsize / closestGhostDistance
                    # if the closest capsule distance is smaller than the closest border distance
                    if closestCapsuleDistance < closestBorderDistance:
                        # updating score by minus the closest capsule distance
                        score -= closestCapsuleDistance
                    # else it is larger
                    else:
                        # updating score
                        score -= closestBorderDistance
                    if isDeadEnd(self, gameState, currAgent.getPosition()):
                        score -= sys.maxsize
                else:
                    score += getFindingFoodEval()

        # else if agent is defensive
        else:
            # if current agent now is pacman
            if currAgent.isPacman:
                return -sys.maxsize
            # happen at the start of program
            if self.targetingFood is None:
                distanceToFood, self.targetingFood = 0, self.initPos
                if currDefendingFood:
                    distanceFoodList = []
                    for food in currDefendingFood:
                        distanceToBorder = min([retrieveMazeDistance(self, border, food) for border in self.borders])
                        distanceFoodList.append((distanceToBorder, food))
                    self.targetingFood = min(distanceFoodList)[1]
                    # distanceToFood = retrieveMazeDistance(self, currPos, self.targetingFood)

            def getTargetingFoodDist():
                if currDefendingFood:
                    if self.targetingFood == currPos:
                        self.isPatrolling = True
                    # if the previous food is not the same as current
                    if prevDefendingFood != currDefendingFood:
                        # pacman will go to the food that has been eaten
                        lostFoods = list(set(prevDefendingFood).difference(currDefendingFood))
                        # if food has been eaten
                        if lostFoods:
                            # get the distance of the closest eaten food
                            closestLostFood = min([(retrieveMazeDistance(self, currPos, food), food) for food in lostFoods])[1]
                            # get the next closest food distance
                            closestNextFoodDistance, closestNextFood = min([(retrieveMazeDistance(self, food, closestLostFood), food) for food in currDefendingFood])
                            # if pacman is patrolling
                            if self.isPatrolling:
                                # then head to the target food which is the next closest food
                                self.targetingFood = closestNextFood
                            # else it is not patrolling
                            else:
                                # if the distance of next closest food is smaller than the targeting food, then make it head to the target food which is the next closest food
                                if retrieveMazeDistance(self, closestNextFood, currPos) < retrieveMazeDistance(self, self.targetingFood, currPos):
                                    self.targetingFood = closestNextFood
                    # if pacman is patrolling
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
                            distance, self.targetingFood = max([(retrieveMazeDistance(self, self.initPos, food), food) for food in nextFood])
                    return retrieveMazeDistance(self, currPos, self.targetingFood)
                return 0

            currEnemyPacmanIndices, currEnemyPacmanStates = [], []
            for idx in getEnemies(self, gameState)[0]:
                enemy = gameState.getAgentState(idx)
                if enemy.isPacman:
                    currEnemyPacmanIndices.append(idx)
                    currEnemyPacmanStates.append(enemy)

            if len(currEnemyPacmanStates) > 0:
                self.isPatrolling = True  # True but actually doesnt patrol but chase the pacman instead, but after chasing, it will continue patrolling
                # the first defender should always chase the pacman
                # the second will patrol the foods until there is the second pacman
                targetPacmanDistance, targetPacmanIdx = min([(retrieveMazeDistance(self, currPos, gameState.getAgentPosition(idx)), idx) for idx in currEnemyPacmanIndices])
                score -= 1000 * targetPacmanDistance
                score -= 100000 * len(currEnemyPacmanStates)
            else:  # If doesn't detect any enemies, just patrolling around the foods
                score -= getTargetingFoodDist()

        # print("Evaluation done")
        return score

    def chooseAction(self, gameState):
        currAgent = gameState.getAgentState(self.index)
        currPos = gameState.getAgentPosition(self.index)
        currCapsules = self.getCapsulesYouAreDefending(gameState)
        currFood = self.getFood(gameState).asList()

        if len(currFood) <= 2 and self.isOffensive:
            action = ucs(self, gameState, currPos, self.borders)[0]
            return action

        currDefendingFood = self.getFoodYouAreDefending(gameState).asList()
        previousState = self.getPreviousObservation()
        prevAgent = currAgent
        if previousState:
            prevAgent = previousState.getAgentState(self.index)
        if self.getScore(gameState) >= self.scoreLimit:
            self.isOffensive = False
        else:
            self.isOffensive = True

        if self.isRetreating and currPos in self.borders:
            self.isRetreating = False

        if currFood:
            if self.isOffensive and getClosestObject(self, currPos, currFood)[0] > getClosestObject(self, currPos, self.borders)[0] and currAgent.numCarrying >= self.maxFoodLimit:
                self.isRetreating = True

        enemyGhostIndices, enemyGhostStates = [], []
        enemyPacmanIndices, enemyPacmanStates = [], []
        for idx in getEnemies(self, gameState)[0]:
            enemy = gameState.getAgentState(idx)
            if enemy.isPacman:
                enemyPacmanIndices.append(idx)
                enemyPacmanStates.append(enemy)
            else:
                if enemy.scaredTimer <= self.scaredTimerLimit:
                    self.lastGhostSeen[idx] = enemy.getPosition()
                    if retrieveMazeDistance(self, currPos, enemy.getPosition()) <= self.detectDistance:
                        enemyGhostIndices.append(idx)
                        enemyGhostStates.append(enemy)
                else:
                    self.lastGhostSeen[idx] = None

        enemyDistanceList = []
        indices = [self.index]
        for idx in enemyGhostIndices:
            enemyGhostState = gameState.getAgentState(idx)
            distance = retrieveMazeDistance(self, currPos, enemyGhostState.getPosition())
            enemyDistanceList.append((distance, idx))
        for idx in enemyPacmanIndices:
            enemyPacmanState = gameState.getAgentState(idx)
            distance = retrieveMazeDistance(self, currPos, enemyPacmanState.getPosition())
            enemyDistanceList.append((distance, idx))
        if enemyDistanceList:
            closestEnemyDistance, closestEnemyIdx = min(enemyDistanceList)
            if self.isOffensive: # attacking
                if closestEnemyIdx in enemyPacmanIndices:
                    self.isOffensive = False
                indices += [closestEnemyIdx]
            else: # defending
                if closestEnemyIdx in enemyGhostIndices: # change to pacman
                    if enemyPacmanIndices:
                        pacmanDistance, closestEnemyIdx = min([(retrieveMazeDistance(self, currPos, gameState.getAgentPosition(idx)), idx) for idx in enemyPacmanIndices])
                        indices += [closestEnemyIdx]
                self.lastGhostSeen = {}

        if currAgent.scaredTimer > 0:
            self.isOffensive = True

        return self.expectimax(gameState, self.maxDepth, indices)[1]


class FlexibleAgentTwo(CaptureAgent):
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
        self.enemyBorders = []
        self.borderX = 0
        self.enemyBorderX = 0
        if self.red:
            self.borderX = self.width - 1
            self.enemyBorderX = self.borderX + 1
        else:
            self.borderX = self.width
            self.enemyBorderX = self.borderX - 1
        for i in range(self.height):
            pos1 = (self.borderX, i)
            if not gameState.hasWall(pos1[0], pos1[1]):
                self.borders.append(pos1)
            pos2 = (self.enemyBorderX, i)
            if not gameState.hasWall(pos2[0], pos2[1]):
                self.enemyBorders.append(pos2)
        self.isFirstDefender = True
        self.initFood = copy.deepcopy(self.getFood(gameState).asList())
        self.hDict = {}
        self.maxDepth = 2
        self.defendingFood = None
        self.enemyPacmanCurrentPosition = None
        self.visitedFood = []
        self.isPatrolling = True
        self.isOffensive = False

        if self.initFood:
            self.scoreToChangeToDefender = math.floor((len(self.initFood) - 2) / 6)
            self.scoreToChangeToOffender = math.floor((len(self.initFood) - 2) / 3) * -1
        else:
            self.scoreToChangeToDefender = 0
            self.scoreToChangeToOffender = -100


        self.isRetreating = False
        self.partnerIndex = copy.deepcopy(self.getTeam(gameState))
        self.partnerIndex.remove(self.index)
        self.partnerIndex = self.partnerIndex[0]
        self.detectDistance = 6
        self.scaredTimerLimit = 5
        self.foodLimit = 2
        self.maxFoodCarryLimitNearBorder = 3
        self.lastGhostSeen = {}
        self.firstTimeAttacking = True
        self.lastGhostSeenTimer = 15
        self.predictingFood = None
        # see as wall parameters
        self.seeEnemyBorderAsWall = False
        self.isGoingForSafeFoodOnly = False
        self.seeFriendAsWall = False

    def chooseAction(self, gameState):
        currAgent = gameState.getAgentState(self.index)
        currPos = gameState.getAgentPosition(self.index)
        currCapsules = self.getCapsules(gameState)
        enemyIndices, enemyStates = getEnemies(self, gameState)
        currFood = self.getFood(gameState).asList()


        otherAgentPos = gameState.getAgentPosition(self.partnerIndex)
        otherAgentClosestFood = getClosestObject(self, otherAgentPos, currFood)[1]

        closestFoodDistance, closestFood = getClosestObject(self, self.initPos, currFood)
        # This agent will attack first but when he detects enemy pacman, he will change to defensive and go for that
        # enemy first. These codes below will use to predict the food at the initial state of the game and he will attack
        # but after he goes to the predicting food first.
        if closestFood and self.predictingFood is None:
            # predict where their closest food is based on our closest food and inverse it
            fx = abs(closestFood[0] - self.enemyBorderX)
            fy = abs(self.height - closestFood[1]) - 1
            if self.red:
                # different positions depending on side
                self.predictingFood = (self.borderX - fx, fy)
            else:
                self.predictingFood = (self.borderX + fx, fy)

        # After he reaches the predicting food, then he attack (if no enemy pacman nearby or he will chase it)
        if currPos == self.predictingFood and self.firstTimeAttacking:
            self.firstTimeAttacking = False

        currDefendingFood = self.getFoodYouAreDefending(gameState).asList()
        previousState = self.getPreviousObservation()
        prevAgent = currAgent
        if previousState:
            prevAgent = previousState.getAgentState(self.index)
            prevDefendingFood = self.getFoodYouAreDefending(previousState).asList()
        else:
            prevDefendingFood = []
        timeLeft = gameState.data.timeleft
        timeEachMove = 4

        if not self.firstTimeAttacking:
            # agent will which to defender if the score is high enough
            if self.getScore(gameState) >= self.scoreToChangeToDefender:
                # defending
                self.isOffensive = False
            else:
                # attacking
                self.isOffensive = True

        pacmanList = []
        # keep track on enemy pacman
        if enemyIndices:
            for idx in enemyIndices:
                enemy = gameState.getAgentState(idx)
                if enemy.isPacman:
                    pacmanList.append(enemy.getPosition())

        # If there are enemy pacman nearby, change to defensive and chase that pacman
        if pacmanList:
            self.isOffensive = False

        # if time is running out agent will switch to defensive
        if timeLeft <= 200:
            self.isOffensive = False

        if currAgent.scaredTimer > 0:
            self.isOffensive = True

        lastGhostSeenCounter(self)
        action = "Stop"
        # attacking
        if self.isOffensive:
            if currAgent.isPacman:
                distanceToBorder = retrieveMazeDistance(self, currPos, getClosestObject(self, currPos, self.borders)[1])
                # if there are no time left, return to border to return the food we are carrying
                if timeLeft <= (distanceToBorder + 2) * timeEachMove:
                    action = astar(self, gameState, self.borders)[0]
                else:
                    ghostList = []
                    if enemyIndices:
                        for idx in enemyIndices:
                            enemy = gameState.getAgentState(idx)
                            if enemy.scaredTimer < self.scaredTimerLimit and not enemy.isPacman:
                                # if enemy is ghost and enemy is not scared, we save the location so that we will see
                                # it as a wall
                                self.lastGhostSeen[idx] = (enemy.getPosition(), self.lastGhostSeenTimer)
                                if retrieveMazeDistance(self, currPos, enemy.getPosition()) <= self.detectDistance:
                                    ghostList.append(enemy.getPosition())
                            else:
                                self.lastGhostSeen[idx] = None
                    # if there are ghosts nearby
                    if ghostList:
                        closestGhostDistance, closestGhost = getClosestObject(self, currPos, ghostList)
                        # if we are carrying some food, return to the border
                        if currAgent.numCarrying >= self.maxFoodCarryLimitNearBorder:
                            action = astar(self, gameState, self.borders)[0]
                        # else (we are not carrying any food or carrying not enough food, then we continue our journey)
                        else:
                            # if you are closer to the capsule then to the ghost
                            capsuleReachable = False
                            closestCapsule = self.initPos
                            if currCapsules:
                                closestCapsuleDistance, closestCapsule = getClosestObject(self, currPos, currCapsules)
                                distanceFromGhostToCapsule = retrieveMazeDistance(self, closestCapsule, closestGhost)
                                if closestCapsuleDistance < distanceFromGhostToCapsule:
                                    capsuleReachable = True
                            if capsuleReachable:
                                # if capsule is closer go for it
                                action = astar(self, gameState, [closestCapsule])[0]
                            else:
                                # if ghost is closer go to the border
                                action = astar(self, gameState, self.borders)[0]
                    # if there are no ghosts nearby
                    else:
                        # if agent is carrying enough food
                        if currAgent.numCarrying >= self.maxFoodCarryLimitNearBorder:
                            nextFoodDistance = getClosestObject(self, currPos, currFood)[0]
                            # if the food is close enough go for it
                            if nextFoodDistance <= 2:
                                action = astar(self, gameState, currFood)[0]
                            # if its not close agent will go to the border
                            else:
                                action = astar(self, gameState, self.borders)[0]
                        else:
                            # if there are more than 2 food left, go for food, else return
                            if len(currFood) > self.foodLimit:
                                action = astar(self, gameState, currFood)[0]
                            else:
                                action = astar(self, gameState, self.borders)[0]
            else:
                if currFood:
                    # go to the current food
                    action = astar(self, gameState, currFood)[0]
                else:
                    # the pacman will return to the border to be defensive
                    self.isOffensive = False
                    action = astar(self, gameState, self.borders)[0]
        # defending
        else:
            if currDefendingFood:
                # the pacman is patrolling the food
                if self.defendingFood == currPos:
                    self.isPatrolling = True
                # if the previous food is not the same as current
                if prevDefendingFood != currDefendingFood:
                    # pacman will go to the food that has been eaten
                    lostFoods = list(set(prevDefendingFood).difference(currDefendingFood))
                    if lostFoods:
                        closestLostFood = getClosestObject(self, currPos, lostFoods)[1]
                        closestNextFoodDistance, closestNextFood = getClosestObject(self, closestLostFood,
                                                                                    currDefendingFood)
                        if self.isPatrolling:
                            self.defendingFood = closestNextFood
                        else:
                            if retrieveMazeDistance(self, closestNextFood, currPos) < \
                                    retrieveMazeDistance(self, self.defendingFood, currPos):
                                self.defendingFood = closestNextFood
                # If we are patrolling, these lines will update the targeting food so that he will patrol thru all the food
                if self.isPatrolling:
                    # check if the ghost has reached targeting food
                    if self.defendingFood == currPos:
                        # add targeted food to list of food defended
                        self.visitedFood.append(self.defendingFood)
                        # update the list of food based on difference of the current food and the defended food
                        nextFood = list(set(copy.deepcopy(currDefendingFood)).difference(self.visitedFood))
                        # if we reached all the food, we need reset the route
                        if not nextFood:
                            self.visitedFood = []
                            nextFood = copy.deepcopy(currDefendingFood)
                        distance, self.defendingFood = getFurthestObject(self, self.initPos, nextFood)

            if self.defendingFood is None:
                closestFoodDistance, closestFood = getClosestObject(self, self.initPos, currFood)
                fx = abs(closestFood[0] - self.enemyBorderX)
                fy = abs(self.height - closestFood[1]) - 1
                if self.red:
                    self.defendingFood = (self.borderX - fx, fy)
                else:
                    self.defendingFood = (self.borderX + fx, fy)
            else:
                self.seeFriendAsWall = False
                # target an enemy pacman
                if pacmanList:
                    targetDistance, targetPacman = getClosestObject(self, currPos, pacmanList)
                    distanceToPartner = retrieveMazeDistance(self, targetPacman, gameState.getAgentPosition(self.partnerIndex))
                    # if the partner is closer see them as a wall to predict the enemy's path
                    if distanceToPartner <= targetDistance:
                        self.seeFriendAsWall = True
                    # target the enemy pacman
                    return astar(self, gameState, [targetPacman])[0]
                else:
                    if currPos == self.defendingFood:
                        # add current food to a list of foods visited
                        self.visitedFood.append(self.defendingFood)
                        for food in currDefendingFood:
                            if food not in self.visitedFood:
                                # if a food has not been visited, go to it
                                if retrieveMazeDistance(self, food, self.defendingFood) <= 3:
                                    self.visitedFood.append(food)
                        nextFoods = list(set(copy.deepcopy(currDefendingFood)).difference(self.visitedFood))
                        # if all foods have been visited
                        if not nextFoods:
                            self.visitedFood = []
                            # make a new list of the current food to defend
                            nextFoods = copy.deepcopy(currDefendingFood)
                        distance, self.defendingFood = getClosestObject(self, currPos, nextFoods)
            return astar(self, gameState, [self.defendingFood])[0]
        return action

def addPositionHistory(self, position):
    # if the agent is attacking
    if self.isAttacking:
        # record their positions in a list
        if len(self.positionHistory.list) >= self.positionHistoryLimit:
            self.positionHistory.pop()
        self.positionHistory.push(position)

def addActionHistory(self, action):
    # record agents action history
    if len(self.actionHistory.list) >= self.actionHistoryLimit:
        self.actionHistory.pop()
    self.actionHistory.push(action)

def retrieveMazeDistance(self, pos1, pos2):
    # retrieve the maze distance between two positions
    distance = max(self.hDict.get((pos1, pos2), -1), self.hDict.get((pos2, pos1), -1))
    if distance != -1:
        return distance
    distance = self.getMazeDistance(pos1, pos2)
    self.hDict[(pos1, pos2)] = distance
    return distance

def getEnemies(self, gameState):
    # Retrieve enemy indices and state
    opponentIndices = self.getOpponents(gameState)
    enemies = [gameState.getAgentState(i) for i in opponentIndices]
    opponentInsightIndices = []
    for idx, e in enumerate(enemies):
        if e.getPosition() != None:
            opponentInsightIndices.append(opponentIndices[idx])
    return opponentInsightIndices, [gameState.getAgentState(i) for i in opponentInsightIndices]

def getClosestObject(self, position, objectList):
    # return the closest object from a certain position
    if objectList:
        return min([(retrieveMazeDistance(self, position, obj), obj) for obj in objectList])
    else:
        return sys.maxsize, None

def getFurthestObject(self, position, objectList):
    # retrieve the furthest object from a certain position
    if objectList:
        return max([(retrieveMazeDistance(self, position, obj), obj) for obj in objectList])
    else:
        return -sys.maxsize, None

def checkLastGhostSeen(self, position):
    # check the position of the last seen ghost
    for key in self.lastGhostSeen:
        if self.lastGhostSeen[key]:  # if not none
            ghostPos = self.lastGhostSeen[key][0]
            if checkPositionNearGhost(self, position, ghostPos):
                return True
    return False

def checkPositionNearGhost(self, position, ghostPosition):
    # check position around the ghost
    for x in range(-1, 2):
        if position == (ghostPosition[0] + x, ghostPosition[1]):
            return True
    for y in range(-1, 2):
        if position == (ghostPosition[0], ghostPosition[1] + y):
            return True
    return False

def isDeadEnd(self, gameState, position, checkAdj=True):
    # check if there is a dead end, with checkAdj is true, mean we will also look at adjacent position for dead end as well
    x = int(position[0])
    y = int(position[1])
    if checkAdj:
        wallCount = 0
        nextPath = []
        if gameState.hasWall(x + 1, y):
            wallCount += 1
        else:
            nextPath.append((x + 1, y))
        if gameState.hasWall(x - 1, y):
            wallCount += 1
        else:
            nextPath.append((x - 1, y))
        if gameState.hasWall(x, y - 1):
            wallCount += 1
        else:
            nextPath.append((x, y - 1))
        if gameState.hasWall(x, y + 1):
            wallCount += 1
        else:
            nextPath.append((x, y + 1))
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
                    return True
        return False
    else:
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
            return True
        else:
            return False

def areAllSafeFoodEaten(self, gameState):
    # check if all the safe food are eaten
    return len(getSafeFood(self, gameState)) == 0

def getSafeFood(self, gameState):
    # make a list of safe food to east
    foodList = self.getFood(gameState).asList()
    return [food for food in foodList if not isDeadEnd(self, gameState, food)]

def isWall(self, gameState, position):
    # check if a position is a wall
    if gameState.hasWall(position[0], position[1]):
        return True
    if self.seeFriendAsWall:
        if position == gameState.getAgentPosition(self.partnerIndex):
            return True
    if self.seeEnemyBorderAsWall:
        if position in self.enemyBorders:
            return True
    return False

def getSuccessorPosition(self, gameState, position):
    successors = []
    if not isWall(self, gameState, (position[0] + 1, position[1])) and not checkLastGhostSeen(self, (position[0] + 1, position[1])):
        successors.append(((position[0] + 1, position[1]), "East"))
    if not isWall(self, gameState, (position[0] - 1, position[1])) and not checkLastGhostSeen(self, (position[0] - 1, position[1])):
        successors.append(((position[0] - 1, position[1]), "West"))
    if not isWall(self, gameState, (position[0], position[1] + 1)) and not checkLastGhostSeen(self, (position[0], position[1] + 1)):
        successors.append(((position[0], position[1] + 1), "North"))
    if not isWall(self, gameState, (position[0], position[1] - 1)) and not checkLastGhostSeen(self, (position[0], position[1] - 1)):
        successors.append(((position[0], position[1] - 1), "South"))
    return successors

def getSuccessorState(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    return successor

def getCostOfActions(self, gameState, start, actions):
    (x, y) = start
    cost = 0
    for action in actions:
        # figure out the next state and see whether it's legal
        dx, dy = Actions.directionToVector(action)
        x, y = int(x + dx), int(y + dy)
        if gameState.hasWall(x, y):
            return 999999
        cost += 1
    return cost

def ucs(self, gameState, endStates):
    start = gameState.getAgentPosition(self.index)
    if start in endStates:
        return [Directions.STOP]
    frontier = util.PriorityQueue()
    frontier.push((start, []), 0)
    visited_states = []
    while not frontier.isEmpty():
        (current, result_path) = frontier.pop()
        if current in endStates:
            return result_path
        if current not in visited_states:
            visited_states.append(current)
            for successor in getSuccessorPosition(self, gameState, current):
                if successor[0] not in visited_states:
                    frontier.push((successor[0], result_path + [successor[1]]), getCostOfActions(self, gameState, start, result_path + [successor[1]]))
    return [Directions.STOP]  # should not reach this


def heuristic(self, gameState, successorPos):
    # Astar's heuristic function for both offensive and denfensive
    # If we are defensive, then we will avoid enemy pacman if we are scared
    # If we are offensive, then we will avoid enemy ghosts
    cost = 0
    enemyIndices, enemyStates = getEnemies(self, gameState)

    agent = gameState.getAgentState(self.index)
    if agent.scaredTimer > 0 and not agent.isPacman:
        pacmanList = []
        if enemyIndices:
            for idx in enemyIndices:
                enemy = gameState.getAgentState(idx)
                if enemy.isPacman:
                    pacmanList.append(enemy.getPosition())
        if pacmanList:
            closestPacmanDistance, closestPacman = getClosestObject(self, successorPos, pacmanList)
            if closestPacmanDistance == 0:
                return sys.maxsize
            else:
                cost += closestPacmanDistance * 100
    else:
        ghostList = []
        if enemyIndices:
            for idx in enemyIndices:
                enemy = gameState.getAgentState(idx)
                if enemy.scaredTimer <= self.scaredTimerLimit and not enemy.isPacman and retrieveMazeDistance(self, successorPos, enemy.getPosition()) <= self.detectDistance:
                    ghostList.append(enemy.getPosition())
        if ghostList:
            closestGhostDistance, closestGhost = getClosestObject(self, successorPos, ghostList)
            if closestGhostDistance == 0:
                return sys.maxsize
            else:
                cost += closestGhostDistance * 100
    return cost

def astar(self, gameState, endStates):
    start = gameState.getAgentPosition(self.index)
    if start in endStates:
        return [Directions.STOP]
    frontier = util.PriorityQueue()
    frontier.push((start, []), 0)
    visited_states = []
    while not frontier.isEmpty():
        (current, result_path) = frontier.pop()
        if current in endStates:
            return result_path
        if current not in visited_states:
            visited_states.append(current)
            for successor in getSuccessorPosition(self, gameState, current):
                if successor[0] not in visited_states:
                    if self.isOffensive:
                        h = heuristic(self, gameState, successor[0])
                    else:
                        h = 0
                    frontier.push((successor[0], result_path + [successor[1]]), getCostOfActions(self, gameState, start, result_path + [successor[1]]) + h)
    return [Directions.STOP]  # should not reach this


def lastGhostSeenCounter(self):
    # This function is used for the locations of enemy saved in our memory and after some time, we will delete it from the memory
    # Having a counter or a timer can reduce the looping between 2 position if we save the location based on the detect distance
    for key in self.lastGhostSeen:
        if self.lastGhostSeen[key]:
            self.lastGhostSeen[key] = (self.lastGhostSeen[key][0] ,self.lastGhostSeen[key][1] - 1)
            if self.lastGhostSeen[key][1] <= 0:
                # once the counter is 0 there is no last seen ghost
                self.lastGhostSeen[key] = None




