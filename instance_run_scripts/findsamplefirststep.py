# -*- coding: utf-8 -*-
# sample_A-n32-k5.py

import os
import random
import numpy
from json import load
from csv import DictWriter
from deap import base, creator, tools
from timeit import default_timer as timer #for timer
import multiprocessing

# Global constant for individual size
# Check before running
IND_SIZE = 31

# Create Fitness and Individual Classes
creator.create('FitnessMax', base.Fitness, weights=(1.0,))
creator.create('Individual', list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()

# Attribute generator
toolbox.register('indexes', random.sample, range(1, IND_SIZE + 1), IND_SIZE)
# Structure initializers
toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indexes)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)

# GA Tools
def gaVRPTW(pop, instName, unitCost, initCost, waitCost, delayCost, 
            indSize, popSize, cxPb, mutPb, NGen, exportCSV=False, customizeData=False):
    if customizeData:
        jsonDataDir = os.path.join('C:\Users\s.janischka\PycharmProjects\py-ga-VRPTW\data', 'json_customize')  #used to be data
    else:
        jsonDataDir = os.path.join('C:\Users\s.janischka\PycharmProjects\py-ga-VRPTW\data', 'json')  #used to be data
    jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
    with open(jsonFile) as f:
        instance = load(f)

    # Operator registering
    #original
    #toolbox.register('evaluate', core.evalVRPTW, instance=instance, unitCost=unitCost, initCost=initCost, waitCost=waitCost, delayCost=delayCost)
    toolbox.register('evaluate', core.evalVRPTW, instance=instance, unitCost=unitCost, waitCost=waitCost, delayCost=delayCost)
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', core.cxPartialyMatched)
    toolbox.register('mutate', core.mutInverseIndexes)

    pop = pop
    print pop

    # Results holders for exporting results to CSV file
    csvData = []
    print 'Start of evolution'
    # Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    # Debug, suppress print()
    # print '  Evaluated %d individuals' % len(pop)
    # Begin the evolution
    for g in range(NGen):
        # print '-- Generation %d --' % g
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
        # print '  Evaluated %d individuals' % len(invalidInd)
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
        # print '  Min %s' % min(fits)
        # print '  Max %s' % max(fits)
        # print '  Avg %s' % mean
        # print '  Std %s' % std
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
    print 'Best individual: %s' % bestInd
    print 'Fitness: %s' % bestInd.fitness.values[0]
    core.printRoute(core.ind2route(bestInd, instance))
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

    print "before supposed visualisation"
    utils.plotResults()
    #utils.visualizeRoutes(instName, instance, bestInd, containsLightResource=False)
    print "after supposed visualisation"
    return core.ind2route(bestInd, instance)

def main():
    random.seed(64)

    instName = 'Customized_Data'

    unitCost = 1.0
    waitCost = 0.0
    delayCost = 0.0
    initCost = 0.0
    indSize = IND_SIZE
    popSize = 100
    cxPb = 0.8
    mutPb = 0.1
    NGen = 100

    exportCSV = True
    customizeData = True

    # Initialize the population.
    # This method can't be parallelized at the moment
    pop = toolbox.population(n=popSize)

    bestIndividual = gaVRPTW(
        pop=pop,
        instName=instName,
        unitCost=unitCost,
        initCost=initCost,
        waitCost=waitCost,
        delayCost=delayCost,
        indSize=indSize,
        popSize=popSize,
        cxPb=cxPb,
        mutPb=mutPb,
        NGen=NGen,
        exportCSV=exportCSV,
        customizeData=customizeData
    )

    print bestIndividual
    return

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from gavrptw import core, utils
    else:
        from ..gavrptw import core, utils
    pool = multiprocessing.Pool()
    toolbox.register('map', pool.map)

    tic = timer()
    main()
    print 'Computing Time: %s' % (timer() - tic)

    pool.close()