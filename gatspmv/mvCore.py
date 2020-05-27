"""mvcore.py docstring

This module includes function required for the genetic algorithm
process to solve a travelling salesman problem with movement synchronization

Todo:
    * Combine the evalution method with the eval() method from core.py
    * Greedy search based on customer demand
"""

import os
import random
import numpy
from json import load
from csv import DictWriter
from deap import base, creator, tools

def distanceList(instance, individual):
    # Use the distance matrix and find the distances between all the
    # customers in the TSP tour
    # NOTE: this distance list has depot and first customer, but not the last
    # customer back to depot!
    distance = []
    lastCustomerID = 0
    for customerID in individual:
        distance.append(instance['distance_matrix'][lastCustomerID][customerID])
        lastCustomerID = customerID
    return distance

def demandList(instance, individual):
    # Use the distance matrix and find the demand of all the
    # customers in the TSP tour
    demand = []
    for customerID in individual:
        demand.append(instance['customer_%d' % customerID]['demand'])
    return demand

def culmulativeDistance(instance, individual, startIndex, endIndex):
    # Returns the distance between the start and end index of customers.
    # If the customer is at the beginning or end, includes the depot
    distList = distanceList(instance, individual)

    if startIndex == 0 or endIndex > len(individual):
        distance = 9999999999999999999
    elif endIndex < len(individual):
        distance = sum(distList[startIndex:endIndex+1])
    elif endIndex == len(individual):
        distance = sum(distList[startIndex:endIndex+1])
        distance += instance['distance_matrix'][individual[endIndex-1]][0]
    return distance

def culmulativeDemand(instance, individual, startIndex, endIndex):
    # Returns the total demand of the start and end index of customers.
    dmdList = demandList(instance, individual)
    demand = sum(dmdList[startIndex:endIndex+1])
    return demand

def distanceBetweenCustomers(instance, fromCustomer, toCustomer):
    return instance['distance_matrix'][fromCustomer][toCustomer]

def splitLightCustomers(instance, individual, lightRange=100, lightCapacity=50):
    # The method takes in a TSP tour, the light resource's
    # range and capacity constraint
    # Returns a list indicating customers that the light resource
    # is able to deliver to - [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
    # The range will include the rendezvous points
    # The capacity does not include the rendezvous points
    considerList = [False] * len(individual) #zero list with length of individual
    considerList[0] = True
    considerList[-1] = True
    clusterList = [0] * len(individual) #zero list with length of individual

    # Determine the order of the distance list
    #distance list is distance from to the customer (does include depot to first but not last to depot)
    distList = distanceList(instance, individual)
    print distList
    sortedDistanceList= [0] * len(distList)
    for i, x in enumerate(sorted(range(len(distList)), key=lambda y: distList[y])):
        sortedDistanceList[x] = i

    # Start the cluster with the closest pair and add neighbouring customers until
    # the range or capacity constraint is reached. Then find the next closest pair
    # not part of any cluster and repeat until all customers are considered
    for i in range(len(individual)):
        considerCustomer = sortedDistanceList.index(i)
        print "consider customer index: %d" % considerCustomer
        # Determine the neighbouring nodes of the considerCustomer
        # Calculate the distance (include rendezvous)
        if considerCustomer == 0:
            clusterEdgeLocation = [considerCustomer, considerCustomer+1]
            distance = 99999999999 #don't consider the first customer as light resource deliverable
        elif considerCustomer == (len(individual)-1):
            clusterEdgeLocation = [considerCustomer-1, considerCustomer]
            distance = 99999999999 #don't consider the last customer as light resource deliverable
        else:
            clusterEdgeLocation = [considerCustomer-1, considerCustomer+1]
            distance = culmulativeDistance(instance, individual,
                                        clusterEdgeLocation[0], clusterEdgeLocation[1])

        # Calculate the demand of considerCustomer
        demand = culmulativeDemand(instance, individual, considerCustomer, considerCustomer)

        # First check if the customer is already considered, range feasibility and demand feasibility
        if (any(considerList[clusterEdgeLocation[0]:clusterEdgeLocation[1]+1]) == True
                or distance > lightRange or demand > lightCapacity):
            continue
        # Passes all tests, initialize considerCustomer as lightCluster
        else:
            considerList[clusterEdgeLocation[0]:clusterEdgeLocation[1]+1] = [True] * (clusterEdgeLocation[1]-clusterEdgeLocation[0]+1)
            clusterList[considerCustomer] = 1

            # Incrementally add the neighbouring customers until the edge of cluster reaches the ends of the list
            # Check range feasibility
            # Check demand feasibility
            while clusterEdgeLocation[0] != 0 or clusterEdgeLocation[1]+1 != len(individual):
                distanceForward = culmulativeDistance(instance, individual,
                                                    clusterEdgeLocation[0], clusterEdgeLocation[1]+1)
                distanceBackward = culmulativeDistance(instance, individual,
                                                    clusterEdgeLocation[0]-1, clusterEdgeLocation[1])
                demandForward =  culmulativeDemand(instance, individual,
                                                    clusterEdgeLocation[0]+1, clusterEdgeLocation[1])
                demandBackward = culmulativeDemand(instance, individual,
                                                    clusterEdgeLocation[0], clusterEdgeLocation[1]-1)
                print "Demand from %d to %d is: %d" % (clusterEdgeLocation[0]+1, clusterEdgeLocation[1], demandForward)
                print "Demand from %d to %d is: %d" % (clusterEdgeLocation[0], clusterEdgeLocation[1]-1, demandBackward)
                print "Range is: %d and %d" % (distanceForward, distanceBackward)

                # Greedy approach: look at the shortest distance neighbouring node to add to cluster
                # If neighbouring node succesfully pass the demand and range constraint
                # Update the cluster list and the consider list
                # Also check if there is a space for light resource to rendezvous
                if (distanceForward <= distanceBackward and distanceForward < lightRange and demandForward < lightCapacity
                    and clusterList[clusterEdgeLocation[1]+1] == False):
                    considerList[clusterEdgeLocation[0]+1:clusterEdgeLocation[1]+1] = [True] * (clusterEdgeLocation[1]-clusterEdgeLocation[0])
                    clusterList[clusterEdgeLocation[0]+1:clusterEdgeLocation[1]+1] = [1] * (clusterEdgeLocation[1]-clusterEdgeLocation[0])
                    if clusterEdgeLocation[1]+1 != len(individual)-1:
                        # Make sure you don't add the first node or the end node
                        clusterEdgeLocation[1] = clusterEdgeLocation[1] + 1
                        print "Cluster forwards is added"
                    else:
                        break
                elif (distanceForward > distanceBackward and distanceBackward < lightRange and demandBackward < lightCapacity
                    and clusterList[clusterEdgeLocation[0]-1] == False):
                    considerList[clusterEdgeLocation[0]:clusterEdgeLocation[1]] = [True] * (clusterEdgeLocation[1]-clusterEdgeLocation[0])
                    clusterList[clusterEdgeLocation[0]:clusterEdgeLocation[1]] = [1] * (clusterEdgeLocation[1]-clusterEdgeLocation[0])
                    if clusterEdgeLocation[0]-1 != 0:
                        clusterEdgeLocation[0] = clusterEdgeLocation[0] - 1
                        print "Cluster backwards is added"
                    else: break
                else:
                    break
                print clusterList
                print "The cluster edge is at: %d and %d" % (clusterEdgeLocation[0], clusterEdgeLocation[1])
    return clusterList

def initMVIndividuals(icls, lightList, individual):
    # Custom method to produce individuals for GA
    # individual = [[L], [L], ..., [H]]
    # [L] = [depart, delivery, delivery, ..., rejoin]
    # The current implmentation will create overlapping rendezvous points for consecutive
    # light resource subRoutes. This could be problematic for the "driver-helper" scenario
    # but efficient for "drone" scenario
    print ""
    print "CREATING INDIVIDUALS"

    genome = list()

    # Find the indicies of where lightList change from 0 to 1
    splitLocation = numpy.where(numpy.roll(lightList,1)!=lightList)[0]
    print "splitlocation"
    print splitLocation
    # Split the individual
    splitList = numpy.split(individual, splitLocation)
    print "splitList"
    print splitList

    # Flatten a list of odd elements from the splitList
    heavyGenome = ([item for sublist in splitList[0::2] for item in sublist])
    print "heavyGenome"
    print heavyGenome

    for i in range(2, len(splitList), 2):
        lightGenome = list()
        lightGenome.extend(random.sample(splitList[i-2], 1))
        lightGenome.extend(splitList[i-1])
        lightGenome.extend(random.sample(splitList[i], 1))
        genome.append(lightGenome)

    genome.append(heavyGenome)
    print "genome before returning"
    print genome
    return icls(genome)

def evalTSPMS(MVindividual, instance, unitCost=1.0, waitCost=0, delayCost=0, speed=1,
                                    lightUnitCost=1.0, lightWaitCost=0, lightDelayCost=0, lightSpeed=1):
    # Evaluate the cost of a MVIndividual, created by the initMVIndividual method
    # Includes: init cost, travel cost and delay cost of light and heavy resource
    # speed and lightSpeed are speed reducers for the heavy and light resource respectively
    # Expects the MSindividual to be [[L], [L], ..., [H]] format
    # The waitCost is when the resource has to wait for the arrival of another resource
    # or the beginning of the delivery window
    # The delayCost is when the resource is late to the delivery window

    print " "
    print "WELCOME TO THE EVALUATION BITCHES !!!!! WOOOOOOOOOOOOOOOOOOOOOOOOOOOP WOOOP WOOP "
    print " "
    print "The MV individual"
    print MVindividual

    route = MVindividual
    totalCost = 0
    lightCost = 0
    heavyCost = 0

    # Dictionary to store the heavy arrival time at this customer
    heavyArrivalTime = dict()
    # Dictionary to store the heavy departure time at this customer
    heavyDepartureTime = dict()
    # Dictionary to store the delay time from the heavy POV at this customer
    # Updated as the light resource are rejoining at this customer
    # Calculated as light resource arrival time - heavy resource departure time
    # If value is positive then heavy resource was waiting
    # If value is negative then light resource was waiting
    resourceDelayTime = dict()

    # Update the heavyArrivalTime and heavyDepartureTime of
    # all heavy resource customers, and calculate the heavy travel cost
    lastCustomerID = 0
    heavyTravelTime = 0
    heavyServiceTime = 0
    heavyTimeCost = 0
    heavyTravelCost = 0
    heavyFinishedTime = 0
    for customerID in route[-1]:
        print "customer ID ", customerID
        heavyTravelTime = instance['distance_matrix'][lastCustomerID][customerID] * speed
        print "heavyTravelTime ", heavyTravelTime
        heavyStartTime =  heavyFinishedTime + heavyTravelTime
        print "heavyStartTime ", heavyStartTime
        heavyArrivalTime[str(customerID)] = heavyStartTime
        print "heavyArrivalTime ", heavyArrivalTime
        heavyServiceTime = instance['customer_%d' % customerID]['service_time'] * 2
        print "heavyServiceTime ", heavyServiceTime
        heavyFinishedTime = heavyStartTime + heavyServiceTime
        print "heavyFinishedTime ", heavyFinishedTime
        heavyDepartureTime[str(customerID)] = heavyFinishedTime
        print "heavryDepartureTime ", heavyDepartureTime
        heavyTimeCost = heavyTimeCost + (waitCost * max(instance['customer_%d' % customerID]['ready_time'] - (heavyTravelTime + heavyStartTime), 0)
                            + delayCost * max((heavyStartTime + heavyTravelTime) - instance['customer_%d' % customerID]['due_time'], 0))
        heavyTravelCost = heavyTravelCost + (unitCost * heavyTravelTime)
        lastCustomerID = customerID

    heavyCost = heavyTimeCost + heavyTravelCost + (instance['distance_matrix'][customerID][0] * speed * unitCost)
    print "Heavy cost is: %f" % heavyCost
    print "Heavy time cost: %f" % heavyTimeCost
    print "Heavy travel cost: %f" % heavyTravelCost
    print " "

    # Given the heavyArrivalTime, calculate the light travel time and cost
    # Update the resourceDelayTime accordingly for the rendezvous customer points
    for subLightRoute in route[:-1]:
        lightElapsedTime = 0
        lightTravelTime = 0
        lightServiceTime = 0
        lightTimeCost = 0
        lightTravelCost = 0
        lastCustomerID = subLightRoute[0]
        lightStartTime = heavyArrivalTime[str(subLightRoute[0])]
        # Considers the travel cost and time cost of all light customers except rejoining back
        for customerID in subLightRoute[1:-1]:
            print "customerID ", customerID
            lightTravelTime = instance['distance_matrix'][lastCustomerID][customerID] * lightSpeed
            print "lightTravelTime is between %d and %d is: %f" % (lastCustomerID, customerID, lightTravelTime)
            lightServiceTime = instance['customer_%d' % customerID]['service_time']
            print "lightServicetime ", lightServiceTime
            lightElapsedTime = lightElapsedTime + lightTravelTime + lightServiceTime
            print "lightElapsedTime ", lightElapsedTime
            # Consider any delay or waiting time because the light resource is earlier than customer ready time
            # or later than customer due time
            lightTimeCost = lightTimeCost + (lightWaitCost * max(instance['customer_%d' % customerID]['ready_time'] - (lightElapsedTime + lightStartTime), 0)
                            + lightDelayCost * max((lightStartTime + lightElapsedTime) - instance['customer_%d' % customerID]['due_time'], 0))
            lightTravelCost = lightTravelCost + (lightUnitCost * lightTravelTime)
            lastCustomerID = customerID
        # Add on the last rejoining leg
        lightTravelTime = instance['distance_matrix'][lastCustomerID][subLightRoute[-1]]
        print "last leg travel time between %d and %d is: %f" % (lastCustomerID, subLightRoute[-1], lightTravelTime)
        lightFinishTime = lightStartTime + lightElapsedTime + lightTravelTime
        print "lightStartTime + lightElapsedTime + lightTravelTime", lightStartTime, "  ", lightElapsedTime, " ", lightTravelTime
        print "the finish time is: %f" % lightFinishTime
        lightCost = lightCost + lightTravelCost + lightTimeCost + (lightUnitCost * lightTravelTime)
        # update the resourceDelayTime for the ending customer of the lightSubRoute
        resourceDelayTime[str(subLightRoute[-1])] = min(lightFinishTime - heavyDepartureTime[str(subLightRoute[-1])],
                                                        lightFinishTime - heavyArrivalTime[str(subLightRoute[-1])], key=abs)
        print "resourceDelayTime ", resourceDelayTime
    print "Light cost is: %f" % lightCost

    # Calculate the waiting penalty given the resourceDelayTime
    # If the value is negative, then the light resource waits for the heavy
    # If the value is positive, the the heavy resource waits for the light
    for customerID in resourceDelayTime:
        print "customerID ", customerID
        print "totalcost ", totalCost
        if resourceDelayTime[customerID] <= 0:
            totalCost = totalCost + (lightWaitCost * abs(resourceDelayTime[customerID]))
            print "light waiting for heavy ", totalCost
        else:
            totalCost = totalCost + (waitCost * resourceDelayTime[customerID])
            print "heavy waiting for light ", totalCost
    print "heavyArrivalTime"
    print heavyArrivalTime
    print "heavryDepartureTime"
    print heavyDepartureTime
    print "resourceDelayTime"
    print resourceDelayTime

    print "total cost is: %f" % totalCost

    totalCost = totalCost + lightCost + heavyCost
    print " totalCost + lightCost + heavyCost ",  totalCost, " ", lightCost, "  ", heavyCost
    fitness = 1/totalCost
    return fitness,

def cxSinglePointSwap(ind1, ind2):
    # A customized crossover method for a TSP route with light and heavy resource
    # Takes in two individuals and randomly swaps the rendezvous points of the light
    # resource subroutes, ignores the heavty resource subroute

    # Iterate both individuals simultaneously since ind1 and ind2
    # are the same length
    for (subRoute1, subRoute2) in (zip(ind1[:-1], ind2[:-1])):
        # swap the depart customer if random number is less than 0.5
        if random.uniform(0,1) < 0.5:
            # keep track of the selected values
            temp1 = subRoute1[0]
            temp2 = subRoute2[0]
            # swap the selected values
            subRoute1[0] = temp2
            subRoute2[0] = temp1
        # swap the reunion customer if random number is greater or equal to 0.5
        else: 
            temp1 = subRoute1[-1]
            temp2 = subRoute2[-1]
            subRoute1[-1] = temp2
            subRoute2[-1] = temp1
    return ind1, ind2

# # testing the code
# random.seed(64)

# SAMPLE_VRPMS = [[32, 28, 3, 17, 14, 35, 44, 7, 23], [23, 43, 24], [24, 46, 33, 5, 47, 31, 22], [32, 49, 23, 24, 22]]
# instName = 'P-n50-0'
# isCustomize = True
# # Customize data dir location
# jsonDataDir = os.path.join('data', 'json_customize')
# jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
# with open(jsonFile) as f:
#     instance = load(f)

# cost= evalTSPMS(SAMPLE_VRPMS, instance, unitCost=0.1, waitCost=0.05, delayCost=0.01, speed=5, lightUnitCost=0.06, lightWaitCost=0, lightDelayCost=0.01, lightSpeed=2.5)
# print 1/cost[0]


def writeEval(MVindividual, instance, unitCost=1.0, waitCost=0, delayCost=0, speed=1,
                                    lightUnitCost=1.0, lightWaitCost=0, lightDelayCost=0, lightSpeed=1):
    # Evaluate the cost of a MVIndividual, created by the initMVIndividual method
    # Includes: init cost, travel cost and delay cost of light and heavy resource
    # speed and lightSpeed are speed reducers for the heavy and light resource respectively
    # Expects the MSindividual to be [[L], [L], ..., [H]] format
    # The waitCost is when the resource has to wait for the arrival of another resource
    # or the beginning of the delivery window
    # The delayCost is when the resource is late to the delivery window

    print " "
    print "WELCOME TO THE writing BITCHES !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    print " "
    print "The MV individual"
    print MVindividual

    route = MVindividual
    totalCost = 0
    lightCost = 0
    heavyCost = 0

    # Dictionary to store the heavy arrival time at this customer
    heavyArrivalTime = dict()
    allArrivalTimes = dict()
    # Dictionary to store the heavy departure time at this customer
    heavyDepartureTime = dict()
    allDeparturetime = dict()
    # Dictionary to store the delay time from the heavy POV at this customer
    # Updated as the light resource are rejoining at this customer
    # Calculated as light resource arrival time - heavy resource departure time
    # If value is positive then heavy resource was waiting
    # If value is negative then light resource was waiting
    resourceDelayTime = dict()

    # Update the heavyArrivalTime and heavyDepartureTime of
    # all heavy resource customers, and calculate the heavy travel cost
    lastCustomerID = 0
    heavyTravelTime = 0
    heavyServiceTime = 0
    heavyTimeCost = 0
    heavyTravelCost = 0
    heavyFinishedTime = 0
    for customerID in route[-1]:
        print "customer ID ", customerID
        heavyTravelTime = instance['distance_matrix'][lastCustomerID][customerID] * speed
        print "heavyTravelTime ", heavyTravelTime
        heavyStartTime =  heavyFinishedTime + heavyTravelTime
        print "heavyStartTime ", heavyStartTime
        heavyArrivalTime[str(customerID)] = heavyStartTime
        print "heavyArrivalTime ", heavyArrivalTime
        heavyServiceTime = instance['customer_%d' % customerID]['service_time'] * 2
        print "heavyServiceTime ", heavyServiceTime
        heavyFinishedTime = heavyStartTime + heavyServiceTime
        print "heavyFinishedTime ", heavyFinishedTime
        heavyDepartureTime[str(customerID)] = heavyFinishedTime
        print "heavryDepartureTime ", heavyDepartureTime
        heavyTimeCost = heavyTimeCost + (waitCost * max(instance['customer_%d' % customerID]['ready_time'] - (heavyTravelTime + heavyStartTime), 0)
                            + delayCost * max((heavyStartTime + heavyTravelTime) - instance['customer_%d' % customerID]['due_time'], 0))
        heavyTravelCost = heavyTravelCost + (unitCost * heavyTravelTime)
        lastCustomerID = customerID

    heavyCost = heavyTimeCost + heavyTravelCost + (instance['distance_matrix'][customerID][0] * speed * unitCost)
    print "Heavy cost is: %f" % heavyCost
    print "Heavy time cost: %f" % heavyTimeCost
    print "Heavy travel cost: %f" % heavyTravelCost
    print " "
    allArrivalTimes = heavyArrivalTime
    allDeparturetime = heavyDepartureTime
    print " all arrival - all departure"
    print allArrivalTimes
    print allDeparturetime

    # Given the heavyArrivalTime, calculate the light travel time and cost
    # Update the resourceDelayTime accordingly for the rendezvous customer points
    for subLightRoute in route[:-1]:
        lightElapsedTime = 0
        lightTravelTime = 0
        lightServiceTime = 0
        lightTimeCost = 0
        lightTravelCost = 0
        lastCustomerID = subLightRoute[0]
        lightStartTime = heavyArrivalTime[str(subLightRoute[0])]
        currentime = lightStartTime
        # Considers the travel cost and time cost of all light customers except rejoining back
        for customerID in subLightRoute[1:-1]:
            print "customerID ", customerID
            lightTravelTime = instance['distance_matrix'][lastCustomerID][customerID] * lightSpeed
            # arrival at the first
            allArrivalTimes[str(customerID)] = lightTravelTime + currentime
            print "lightTravelTime is between %d and %d is: %f" % (lastCustomerID, customerID, lightTravelTime)
            lightServiceTime = instance['customer_%d' % customerID]['service_time']
            allDeparturetime[str(customerID)] = currentime + lightServiceTime
            print "lightServicetime ", lightServiceTime
            lightElapsedTime = lightElapsedTime + lightTravelTime + lightServiceTime
            print "lightElapsedTime ", lightElapsedTime
            # Consider any delay or waiting time because the light resource is earlier than customer ready time
            # or later than customer due time
            lightTimeCost = lightTimeCost + (lightWaitCost * max(instance['customer_%d' % customerID]['ready_time'] - (lightElapsedTime + lightStartTime), 0)
                            + lightDelayCost * max((lightStartTime + lightElapsedTime) - instance['customer_%d' % customerID]['due_time'], 0))
            lightTravelCost = lightTravelCost + (lightUnitCost * lightTravelTime)
            lastCustomerID = customerID
        # Add on the last rejoining leg
        lightTravelTime = instance['distance_matrix'][lastCustomerID][subLightRoute[-1]]
        print "last leg travel time between %d and %d is: %f" % (lastCustomerID, subLightRoute[-1], lightTravelTime)
        lightFinishTime = lightStartTime + lightElapsedTime + lightTravelTime
        print "lightStartTime + lightElapsedTime + lightTravelTime", lightStartTime, "  ", lightElapsedTime, " ", lightTravelTime
        print "the finish time is: %f" % lightFinishTime
        lightCost = lightCost + lightTravelCost + lightTimeCost + (lightUnitCost * lightTravelTime)
        # update the resourceDelayTime for the ending customer of the lightSubRoute
        resourceDelayTime[str(subLightRoute[-1])] = min(lightFinishTime - heavyDepartureTime[str(subLightRoute[-1])],
                                                        lightFinishTime - heavyArrivalTime[str(subLightRoute[-1])], key=abs)

        #if drone arrives later than the ssumed departure time of the truck -> make truck delay everywhere
        if lightFinishTime > heavyDepartureTime[str(subLightRoute[-1])]:
            #indeed give everyone delay
            givedelay= lightFinishTime-heavyDepartureTime[str(subLightRoute[-1])]
            heavyDepartureTime[str(subLightRoute[-1])] = heavyDepartureTime[str(subLightRoute[-1])] + givedelay
            allDeparturetime[str(subLightRoute[-1])] = allDeparturetime[str(subLightRoute[-1])] + givedelay

            startproblemsat = str(subLightRoute[-1])
            print "startproblems at ", startproblemsat
            problemshappened = 0
            for customers in route[-1]:
                print "truying to solve delays ", customers
                if problemshappened == 1:
                    heavyArrivalTime[str(customers)] = heavyArrivalTime[str(customers)] + givedelay
                    heavyDepartureTime[str(customers)] = heavyDepartureTime[str(customers)] + givedelay
                    allArrivalTimes[str(customers)] = allArrivalTimes[str(customers)] + givedelay
                    allDeparturetime[str(customers)] = allDeparturetime[str(customers)] + givedelay
                if customers == startproblemsat:
                    problemshappened = 1





        print "resourceDelayTime ", resourceDelayTime
    print "Light cost is: %f" % lightCost

    # Calculate the waiting penalty given the resourceDelayTime
    # If the value is negative, then the light resource waits for the heavy
    # If the value is positive, the the heavy resource waits for the light
    for customerID in resourceDelayTime:
        print "customerID ", customerID
        print "totalcost ", totalCost
        if resourceDelayTime[customerID] <= 0:
            totalCost = totalCost + (lightWaitCost * abs(resourceDelayTime[customerID]))
            print "light waiting for heavy ", totalCost
        else:
            totalCost = totalCost + (waitCost * resourceDelayTime[customerID])
            print "heavy waiting for light ", totalCost
    print "heavyArrivalTime"
    print heavyArrivalTime
    print "heavryDepartureTime"
    print heavyDepartureTime
    print "resourceDelayTime"
    print resourceDelayTime

    print "total cost is: %f" % totalCost

    totalCost = totalCost + lightCost + heavyCost
    print " totalCost + lightCost + heavyCost ",  totalCost, " ", lightCost, "  ", heavyCost
    fitness = 1/totalCost

    #writing
    f= open("custdate.txt", "a+")
    for customer in allArrivalTimes:
        print "printing ", customer
        f.write(customer)
        f.write("\n")
        f.write("arrival %d\n" %allArrivalTimes[customer])
        f.write("departure %d\r\n" % allDeparturetime[customer])
    f.close()

    return fitness,