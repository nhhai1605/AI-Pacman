# firstTeam.py
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

from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MyOffensiveAgent', second = 'MyDefensiveAgent', numTraining = 0):
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

class DummyAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """

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
        # print(self.height)
        # print(self.width)
        # print(gameState.data.layout.walls)
        if gameState.isOnRedTeam(self.index):
            borderX = self.width - 1
            for i in range(self.height):
                pos = (borderX, i)
                if not gameState.hasWall(pos[0], pos[1]):
                    self.borders.append(pos)
        else:
            borderX = self.width
            for i in range(self.height):
                pos = (borderX, i)
                if not gameState.hasWall(pos[0], pos[1]):
                    self.borders.append(pos)
        # print(self.red)
        # print(self.borders)
        self.initDefendingFoodList = self.getFoodYouAreDefending(gameState).asList()
        self.defendingFoodList = self.getFoodYouAreDefending(gameState).asList()
        # self.initFoodList = self.getFood(gameState).asList()
        # self.foodList = self.getFood(gameState).asList()



    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        return successor

    def evaluate(self, gameState, action):
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def chooseAction(self, gameState):
        # actions = gameState.getLegalActions(self.index)
        # actionValueList = [(self.evaluate(gameState,a),a) for a in actions]
        # return max(actionValueList)[1]
        util.raiseNotDefined()

    def getFeatures(self, gameState, action):
        util.raiseNotDefined()

    def getWeights(self, gameState, action):
        util.raiseNotDefined()

    def getCloseGhosts(self, gameState):
        opponentIndices = self.getOpponents(gameState)
        enemies = [gameState.getAgentState(i) for i in opponentIndices]
        opponentInsightIndices = []
        ourAgent = gameState.getAgentState(self.index)
        for idx, e in enumerate(enemies):
            if e.getPosition() != None and not e.isPacman and gameState.getAgentState(self.index).isPacman:
            # if e.getPosition() != None and not e.isPacman:
                distance = self.getMazeDistance(e.getPosition(), ourAgent.getPosition())
                if distance <= 5:
                    opponentInsightIndices.append(opponentIndices[idx])
        return [(i, gameState.getAgentState(i)) for i in opponentInsightIndices]

    def getEnemyPacman(self, gameState):
        opponentIndices = self.getOpponents(gameState)
        enemies = [gameState.getAgentState(i) for i in opponentIndices]
        opponentInsightIndices = []
        # ourAgent = gameState.getAgentState(self.index)
        for idx, e in enumerate(enemies):
            if e.getPosition() != None and e.isPacman and not gameState.getAgentState(self.index).isPacman:
                opponentInsightIndices.append(opponentIndices[idx])
        return [(i, gameState.getAgentState(i)) for i in opponentInsightIndices]

class MyOffensiveAgent(DummyAgent):

    # def chooseAction(self, gameState):
    #     import sys
    #     maxDepth = 2
    #     successor = self.getSuccessor(gameState, "Stop")
    #     indices = [self.index]
    #     opponentInsightIndices = [e[0] for e in self.getCloseGhosts(successor)]
    #     indices += opponentInsightIndices
    #     def maxValue(currentGameState, arrayIndex, currentDepth):
    #         if currentDepth == maxDepth:
    #             return self.evaluate(currentGameState, "Stop"), "Stop"
    #         valueMoveList = [(-sys.maxsize, "Stop")]
    #         for a in currentGameState.getLegalActions(indices[arrayIndex]):
    #             nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
    #             value2, a2 = expectValue(nextState, arrayIndex + 1, currentDepth)
    #             valueMoveList.append((value2, a))
    #         return max(valueMoveList)
    #
    #     def expectValue(currentGameState, arrayIndex, currentDepth):
    #         if currentDepth == maxDepth:
    #             return self.evaluate(currentGameState, "Stop"), "Stop"
    #         if arrayIndex >= len(indices):
    #             arrayIndex = 0
    #             return maxValue(currentGameState, arrayIndex, currentDepth + 1)
    #         value, move = 0, "Stop"
    #         actions = currentGameState.getLegalActions(indices[arrayIndex])
    #         for a in actions:
    #             # print(a)
    #             nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
    #             value2, a2 = expectValue(nextState, arrayIndex + 1, currentDepth)
    #             value += value2
    #             move = a
    #         # print("done")
    #         value /= len(actions)
    #         return value, move
    #
    #     def expectimax(currentGameState, arrayIndex, depth):
    #         value, move = maxValue(currentGameState, arrayIndex, depth)
    #         return value, move
    #
    #     return expectimax(successor, 0, 0)[1]

    def chooseAction(self, gameState):
        import sys
        maxDepth = 2

        successor = self.getSuccessor(gameState, "Stop")
        indices = [self.index]
        opponentInsightIndices = [e[0] for e in self.getCloseGhosts(successor)]
        indices += opponentInsightIndices

        def maxValue(currentGameState, arrayIndex, currentDepth, alpha, beta):
            if currentDepth == maxDepth:
                return self.evaluate(currentGameState, "Stop"), "Stop"
            value = -sys.maxsize
            move = "Stop"
            for a in currentGameState.getLegalActions(indices[arrayIndex]):
                nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
                value2, a2 = minValue(nextState, arrayIndex + 1, currentDepth, alpha, beta)
                if value2 > value:
                    value, move = value2, a
                    alpha = max(alpha, value)
                if value > beta:
                    return value, move
            return value, move

        def minValue(currentGameState, arrayIndex, currentDepth, alpha, beta):
            if currentDepth == maxDepth:
                return self.evaluate(currentGameState, "Stop"), "Stop"
            if arrayIndex >= len(indices):
                arrayIndex = 0
                return maxValue(currentGameState, arrayIndex, currentDepth + 1, alpha, beta)
            value = sys.maxsize
            move = "Stop"
            for a in currentGameState.getLegalActions(indices[arrayIndex]):
                nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
                value2, a2 = minValue(nextState, arrayIndex + 1, currentDepth, alpha, beta)
                if value2 < value:
                    value, move = value2, a
                    beta = min(beta, value)
                if value < alpha:
                    return value, move
            return value, move

        def alphaBeta(currentGameState, arrayIndex, depth):
            value, move = maxValue(currentGameState, arrayIndex, depth, -sys.maxsize, sys.maxsize)
            return value, move

        return alphaBeta(successor, 0, 0)[1]



    def getFeatures(self, gameState, action):
        features = util.Counter()

        successor = self.getSuccessor(gameState, action)
        newFoodList = self.getFood(successor).asList()
        currFoodList = self.getFood(gameState).asList()
        newPos = successor.getAgentState(self.index).getPosition()
        capsuleList = self.getCapsules(successor)



        # Set the pacman to find the food
        def setFoodFeatures():
            if len(newFoodList) > 2:
                features['numFoods'] = len(newFoodList)
                features['distanceToFood'] = min([self.getMazeDistance(newPos, food) for food in newFoodList])
                features['numCapsules'] = len(capsuleList)
            else:
                # features['distanceToBorder'] = min([self.getMazeDistance(newPos, border) for border in self.borders])
                features['distanceToBorder'] = self.getMazeDistance(newPos, self.initPos)

        # get new ghost states and scared times
        newGhostStates = [e[1] for e in self.getCloseGhosts(successor)]
        newScaredTimes = [ghostState.scaredTimer for ghostState in newGhostStates]
        newGhostStates = [ghostState.getPosition() for ghostState in newGhostStates]


        # if len(newGhostStates) > 0:
        #     closestGhostDistance, closestGhost = min([(self.getMazeDistance(newPos, ghostState), ghostState) for ghostState in newGhostStates])
        #     if newScaredTimes[newGhostStates.index(closestGhost)] == 0:
        #         features['ghostDistance'] = 1/closestGhostDistance
        #         features['distanceToBorder'] = min([self.getMazeDistance(newPos, border) for border in self.borders])
        #     else:
        #         closestFoodDistance, closestFood = min([(self.getMazeDistance(newPos, food), food) for food in newFoodList])
        #         if closestFoodDistance < closestGhostDistance:
        #             setFoodFeatures()
        #         else:
        #             features['ghostDistance'] = 0
        #             features['scaredGhostDistance'] = closestGhostDistance
        # else:
        #     setFoodFeatures()

        setFoodFeatures()
        if len(newGhostStates) > 0:
            closestGhostDistance, closestGhost = min([(self.getMazeDistance(newPos, ghostState), ghostState) for ghostState in newGhostStates])
            if newScaredTimes[newGhostStates.index(closestGhost)] == 0:
                features['ghostDistance'] = 1/closestGhostDistance
                features['numFoods'] = 0
                features['distanceToFood'] = 0
                # features['distanceToBorder'] = min([self.getMazeDistance(newPos, border) for border in self.borders])
                features['distanceToBorder'] = self.getMazeDistance(newPos, self.initPos)
            else:
                features['ghostDistance'] = 0
                features['numFoods'] = 0
                features['distanceToFood'] = 0
                features['scaredGhostDistance'] = closestGhostDistance
                # print(features)


        return features

    def getWeights(self, gameState, action):
        return {'numFoods': -100, 'distanceToFood': -1, 'numCapsules': -200, 'ghostDistance': -100, "distanceToBorder": -1, "distanceToBase": -10, "scaredGhostDistance": -100}


class MyDefensiveAgent(DummyAgent):

    # def chooseAction(self, gameState):
    #     import sys
    #     maxDepth = 2
    #     successor = self.getSuccessor(gameState, "Stop")
    #     indices = [self.index]
    #     opponentInsightIndices = [e[0] for e in self.getEnemyPacman(successor)]
    #     indices += opponentInsightIndices
    #     # print(indices)
    #     def maxValue(currentGameState, arrayIndex, currentDepth):
    #         if currentDepth == maxDepth:
    #             return self.evaluate(currentGameState, "Stop"), "Stop"
    #         valueMoveList = [(-sys.maxsize, "Stop")]
    #         for a in currentGameState.getLegalActions(indices[arrayIndex]):
    #             nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
    #             value2, a2 = expectValue(nextState, arrayIndex + 1, currentDepth)
    #             valueMoveList.append((value2, a))
    #         return max(valueMoveList)
    #
    #     def expectValue(currentGameState, arrayIndex, currentDepth):
    #         if currentDepth == maxDepth:
    #             return self.evaluate(currentGameState, "Stop"), "Stop"
    #         if arrayIndex >= len(indices):
    #             arrayIndex = 0
    #             return maxValue(currentGameState, arrayIndex, currentDepth + 1)
    #         value, move = 0, "Stop"
    #         actions = currentGameState.getLegalActions(indices[arrayIndex])
    #         for a in actions:
    #             # print(a)
    #             nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
    #             value2, a2 = expectValue(nextState, arrayIndex + 1, currentDepth)
    #             value += value2
    #             move = a
    #         # print("done")
    #         value /= len(actions)
    #         return value, move
    #
    #     def expectimax(currentGameState, arrayIndex, depth):
    #         value, move = maxValue(currentGameState, arrayIndex, depth)
    #         return value, move
    #
    #     return expectimax(successor, 0, 0)[1]

    def chooseAction(self, gameState):
        import sys
        maxDepth = 2

        successor = self.getSuccessor(gameState, "Stop")
        indices = [self.index]
        opponentInsightIndices = [e[0] for e in self.getEnemyPacman(successor)]
        indices += opponentInsightIndices

        def maxValue(currentGameState, arrayIndex, currentDepth, alpha, beta):
            if currentDepth == maxDepth:
                return self.evaluate(currentGameState, "Stop"), "Stop"
            valueMoveList = [(-sys.maxsize, "Stop")]
            value = -sys.maxsize
            move = None
            for a in currentGameState.getLegalActions(indices[arrayIndex]):
                nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
                value2, a2 = minValue(nextState, arrayIndex + 1, currentDepth, alpha, beta)
                valueMoveList.append((value2, a))
                if value2 > value:
                    value, move = value2, a
                    alpha = max(alpha, value)
                if value > beta:
                    return value, move
            return value, move

        def minValue(currentGameState, arrayIndex, currentDepth, alpha, beta):
            if currentDepth == maxDepth:
                return self.evaluate(currentGameState, "Stop"), "Stop"
            if arrayIndex >= len(indices):
                arrayIndex = 0
                return maxValue(currentGameState, arrayIndex, currentDepth + 1, alpha, beta)
            valueMoveList = [(-sys.maxsize, "Stop")]
            value = sys.maxsize
            move = None
            for a in currentGameState.getLegalActions(indices[arrayIndex]):
                nextState = currentGameState.generateSuccessor(indices[arrayIndex], a)
                value2, a2 = minValue(nextState, arrayIndex + 1, currentDepth, alpha, beta)
                valueMoveList.append((value2, a))
                if value2 < value:
                    value, move = value2, a
                    beta = min(beta, value)
                if value < alpha:
                    return value, move
            return value, move

        def alphaBeta(currentGameState, arrayIndex, depth):
            value, move = maxValue(currentGameState, arrayIndex, depth, -sys.maxsize, sys.maxsize)
            return value, move

        return alphaBeta(successor, 0, 0)[1]

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        ourAgent = successor.getAgentState(self.index)
        newPos = ourAgent.getPosition()
        if ourAgent.isPacman:
            features['onDefense'] = 1

        newEnemyPacmanStates = [e[1] for e in self.getEnemyPacman(successor)]
        # currEnemyPacmanStates = [e[1] for e in self.getEnemyPacman(gameState)]

        if len(newEnemyPacmanStates) > 0:
            features['numInvaders'] = len(newEnemyPacmanStates)
            closestPacmanDistance = min([self.getMazeDistance(newPos, pacmanState.getPosition()) for pacmanState in newEnemyPacmanStates])
            newScaredTime = ourAgent.scaredTimer
            if newScaredTime == 0:
                features['invaderDistance'] = closestPacmanDistance
        else:
            if len(self.initDefendingFoodList) != len(self.getFoodYouAreDefending(gameState).asList()):
                self.initDefendingFoodList = self.getFoodYouAreDefending(gameState).asList()
                self.defendingFoodList = self.getFoodYouAreDefending(gameState).asList()
            if newPos in self.defendingFoodList:
                self.defendingFoodList.remove(newPos)
                if len(self.defendingFoodList) == 0:
                    self.defendingFoodList = self.getFoodYouAreDefending(gameState).asList()
            features['distanceToFood'] = min([self.getMazeDistance(newPos, food) for food in self.defendingFoodList])

        return features

    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': -100, 'invaderDistance': -10, "distanceToFood": -1}
