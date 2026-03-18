#pragma once

#include <boost/program_options.hpp>

#include <mass/Places.h>
#include <mass/Agents.h>

#include <simviz.h>

#include <vector>

namespace po = boost::program_options;

namespace tuberculosis {
    // Simulation configuration options. These are defined in this document:
    // https://docs.google.com/document/d/0B-DdRv6zRAzAS1k1SkJ0aEJ1SDFyTEJWMGlnVDFWVlA3eHhz
    struct ConfigOpts {
        int seed;
        int size;                  
        int total_days;
        int init_macro_num;
    };

    // runSimulation runs the Tuberculosis simulation, configured with the
    // provided options.
    void runSimulation(ConfigOpts opts, int interval, simviz::RGBFile& vizFile);

    // outputSimSpace outputs a graphical visualiztion of the simulation space
    // to the provided simviz file.
    // Each place is represented by a 2x2 grid. The top left pixel is for 
    // the bacteria (black if present).
    // The top right pixel is for the macrophage (resting - green, 
    // infected - yellow, activated - light blue, chronically infected - dark purple).
    // The bottom left pixel is for tcells (bright blue if present).
    // The bottom right pixel represents the chemokine level (1 - orange, 2 - red)
    void outputSimSpace(simviz::RGBFile& vizFile, mass::Places *places, int size);

    // parseSimConfig parses the provided variables_map and
    // returns configs options for which to run the simulation
    // with.
    ConfigOpts parseSimConfig(po::variables_map vm);


    // assigns place ids that are initialized with macrophages to static array macroSpawn
    void spawnInitialMacrophages(int size, int* macroSpawn, int totalMacro);

    // assigns proper place ids to TCell spawners to static array tcellSpawn
    void spawnInitialTCells(int size, int* tcellSpawn);

    // generateRandVals generates 'n' random values, using cstdlib
    // and the provided seed.
    int* generateRandVals(int n);
}