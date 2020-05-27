# -*- coding: utf-8 -*-
# sample_A-n32-k5-VRPMV.py

 
import os
import random
import numpy
from json import load
from csv import DictWriter
from deap import base, creator, tools
from timeit import default_timer as timer #for timer





def main():
    print "printer in def main()"
    # REMOVE FILE AND WRITE NEW
    #os.remove("testprintingAn32K5.txt")
    f = open("custdate.txt", "w+")
    f.write("newfile \n")
    f.close()


    random.seed(64)

    instName = 'Customized_Data'

    unitCost = 2.0
    initCost = 0.0
    waitCost = 0.0
    delayCost = 0.0
    speed = 5
    lightUnitCost = 1.0
    lightInitCost = 0.0
    lightWaitCost = 0.0
    lightDelayCost = 0.0
    lightSpeed = 4
    lightRange = 100
    lightCapacity = 50

    popSize = 200
    cxPb = 0.9
    mutPb = 0
    NGen = 100

    exportCSV = False
    customizeData = True

    # This should be the outcome of running the gavrptw module
    bestVRP = [[1, 3, 11, 13, 26, 28, 23, 22, 20, 21, 25], [2, 5, 6, 19, 16, 15, 7, 8, 9], [10, 18, 17, 12, 14, 31, 29, 30, 24, 27, 4]] #[[1, 6, 3, 8], [10, 4, 7, 9, 5, 2]]
    # bestVRP = [[30, 11, 4, 22, 29, 23, 8, 14], [12, 16, 5, 25, 10, 20], [15, 9, 6, 3, 1, 27, 26], [19, 17, 31, 21, 13, 28, 18], [24, 2, 7]]
    bestVRPMV = []
    bestVRPMVCost = 0

    for tsp in bestVRP:
        indSize = len(tsp)
        # Try first without multiprocessing for this substep
        bestSubTSP, bestSubTSPFitness = gaTSPMV(
            instName=instName,
            tsp=tsp,
            unitCost=unitCost,
            initCost=initCost,
            waitCost=waitCost,
            delayCost=delayCost,
            speed=speed,
            lightUnitCost=lightUnitCost,
            lightInitCost=lightInitCost,
            lightWaitCost=lightWaitCost,
            lightDelayCost=lightDelayCost,
            lightRange=lightRange,
            lightCapacity=lightCapacity,
            lightSpeed=lightSpeed,
            indSize=indSize,
            popSize=popSize,
            cxPb=cxPb,
            mutPb=mutPb,
            NGen=NGen,
            exportCSV=exportCSV,
            customizeData=customizeData
        )
        bestVRPMV.append(bestSubTSP)
        bestVRPMVCost = bestVRPMVCost + 1/bestSubTSPFitness
        print "best VRPMV"
        print bestVRPMV
        print "best VRPMVCost"
        print bestVRPMVCost
    f = open("testprintingAn32K5.txt", "a")
    f.write("the best VRPMV \n")
    f.write(str(bestVRPMV))
    f.close()
    return







# GA Tools
def gaTSPMV(instName, tsp, unitCost, initCost, waitCost, delayCost, speed, indSize, popSize, 
                            lightUnitCost, lightInitCost, lightWaitCost, lightDelayCost, lightSpeed,
                            lightRange, lightCapacity,
                            cxPb, mutPb, NGen, exportCSV=False, customizeData=False):
    print "print in gaTSPMV"
    if customizeData:
        jsonDataDir = os.path.join('C:\Users\s.janischka\PycharmProjects\py-ga-VRPTW\data', 'json_customize')
    else:
        jsonDataDir = os.path.join('data', 'json')
    jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
    with open(jsonFile) as f:
        instance = load(f)



    # Create Fitness and Individual Classes
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()

    #the TSP being treated at this moment
    print "1-  tsp at the moment is:"
    print tsp

    #list representing which customers could be treated by a light resource
    splitLightList = mvcore.splitLightCustomers(instance, tsp, lightRange=lightRange, lightCapacity=lightCapacity)
    toolbox.register('individual', mvcore.initMVIndividuals, creator.Individual, splitLightList, tsp)
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)

    print "2-  the list of light possibilities"
    print splitLightList

    pop = toolbox.population(n=popSize)

    # Operator registering
    #original
    #toolbox.register('evaluate', mvcore.evalTSPMS, instance=instance, unitCost=unitCost, initCost=initCost, waitCost=waitCost, delayCost=delayCost, speed=speed,
    #                                                lightUnitCost=lightUnitCost, lightInitCost=lightInitCost, lightWaitCost=lightWaitCost, lightDelayCost=lightDelayCost, lightSpeed=lightSpeed)

    toolbox.register('evaluate', mvcore.evalTSPMS, instance=instance, unitCost=unitCost, waitCost=waitCost, delayCost=delayCost, speed=speed,
                                                    lightUnitCost=lightUnitCost, lightWaitCost=lightWaitCost, lightDelayCost=lightDelayCost, lightSpeed=lightSpeed)
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', mvcore.cxSinglePointSwap)
    toolbox.register('mutate', core.mutInverseIndexes)

    print "3-  this is the pop"
    print pop

    # Results holders for exporting results to CSV file
    csvData = []
    print 'Start of evolution'
    # Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    print "3.5 fitnesses --"
    print fitnesses

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        print " ind is  ", ind
        print " fit is   ", fit

    # Debug, suppress print()
    print '4-  Evaluated %d individuals' % len(pop)
    # Begin the evolution
    for g in range(NGen):
        print 'a-  -- Generation %d --' % g
        # Select the next generation individuals
        # Select elite - the best offspring, keep this past crossover/mutate
        elite = tools.selBest(pop, 1)
        # Keep top 10% of all offspring
        # Roulette select the rest 90% of offsprings
        offspring = tools.selBest(pop, int(numpy.ceil(len(pop)*0.1)))
        offspringRoulette = toolbox.select(pop, int(numpy.floor(len(pop)*0.9))-1)
        offspring.extend(offspringRoulette)
        # Clone the selected individuals
        offspring = list(toolbox.map(toolbox.clone, offspring))
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxPb:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        for mutant in offspring:
            if random.random() < mutPb:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness
        invalidInd = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
        # Debug, suppress print()
        print 'b--  Evaluated %d individuals' % len(invalidInd)
        # The population is entirely replaced by the offspring
        offspring.extend(elite)
        pop[:] = offspring
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5
        # Debug, suppress print()
        print '  Min %s' % min(fits)
        print '  Max %s' % max(fits)
        print '  Avg %s' % mean
        print '  Std %s' % std
        # Write data to holders for exporting results to CSV file
        if exportCSV:
            csvRow = {
                'generation': g,
                'evaluated_individuals': len(invalidInd),
                'min_fitness': min(fits),
                'max_fitness': max(fits),
                'avg_fitness': mean,
                'std_fitness': std,
                'avg_cost': 1 / mean,
            }
            csvData.append(csvRow)
    print '-- End of (successful) evolution --'
    bestInd = tools.selBest(pop, 1)[0]
    #  HERE I WRITE MY FILE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # make een tweede evaluate - maar dan filewrite
    #verbind op dezelfde manier
    toolbox.register('writefile', mvcore.writeEval, instance=instance, unitCost=unitCost, waitCost=waitCost, delayCost=delayCost, speed=speed,
                                                    lightUnitCost=lightUnitCost, lightWaitCost=lightWaitCost, lightDelayCost=lightDelayCost, lightSpeed=lightSpeed)
    toolbox.writefile(bestInd)
    print " IM HERE NOW"

    print 'Best individual: %s' % bestInd
    print 'Fitness: %s' % bestInd.fitness.values[0]
    print 'Total cost: %s' % (1 / bestInd.fitness.values[0])
    if exportCSV:
        csvFilename = '%s_uC%s_iC%s_wC%s_dC%s_iS%s_pS%s_cP%s_mP%s_nG%s.csv' % (instName, unitCost, initCost, waitCost, delayCost, indSize, popSize, cxPb, mutPb, NGen)
        csvPathname = os.path.join('results', csvFilename)
        print 'Write to file: %s' % csvPathname
        utils.makeDirsForFile(pathname=csvPathname)
        if not utils.exist(pathname=csvPathname, overwrite=True):
            with open(csvPathname, 'w') as f:
                fieldnames = ['generation', 'evaluated_individuals', 'min_fitness', 'max_fitness', 'avg_fitness', 'std_fitness', 'avg_cost']
                writer = DictWriter(f, fieldnames=fieldnames, dialect='excel')
                writer.writeheader()
                for csvRow in csvData:
                    writer.writerow(csvRow)
    return bestInd, bestInd.fitness.values[0]



if __name__ == '__main__':
    print "first printer in if name is main"
    if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from gatspmv import mvCore as mvcore  #this used to be import mvcore but the capital threw the program of
        from gavrptw import core, utils
    else:
        from ..gatspmv import mvCore as mvcore #samesame
        from ..gavrptw import core, utils
    tic = timer()
    main()
    print 'Computing Time: %s' % (timer() - tic)
# The output of the route: [[8, 11, 4, 22, 29, 23, 30, 14], [12, 16, 5, 25, 10, 20], [15, 9, 6, 3, 1, 27, 26], [19, 17, 31, 21, 13, 28, 18], [24, 2, 7]]
# Is the mixed route: [[[11, 4, 22, 29], [8, 11, 29, 23, 30, 14]], [[12, 16, 5, 25, 10, 20]], [[15, 9, 6, 3, 1, 27, 26]], [[19, 31, 21, 13, 28], [19, 17, 28, 18]], [[24, 2, 7]]]
# route 1 light: 11, 4, 22, 29
# route 1 heavy: 0 - 8, 11, 29, 23, 30, 14 - 0
# route 2 light: n/a
# route 2 heavy: 0 - 12, 16, 5, 25, 10, 20 - 0
# route 3 light: n/a
# route 3 heavy: 0 - 15, 9, 6, 3, 1, 27, 26 - 0
# route 4 light: [19, 31, 21, 13, 28]
# route 4 heavy: 0 - 19, 17, 28, 18 - 0
# route 5 light: n/a
# route 5 heavy: 0 - 24, 2, 7 - 0