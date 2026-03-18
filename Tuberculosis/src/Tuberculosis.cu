#include <mass/Mass.h>

#include <iostream>
#include <sstream>  // ostringstream
#include <vector>

#include "EnvironmentPlace.h"
#include "Macrophage.h"
#include "TCell.h"
#include "Tuberculosis.h"

namespace tuberculosis {
void runSimulation(ConfigOpts opts, int interval, simviz::RGBFile& vizFile) {
   mass::logger::info("Starting MASS CUDA Tuberculosis simulation");
   mass::logger::info("MASS Config: MAX_AGENTS=%d, MAX_NEIGHBORS=%d, MAX_DIMS=%d, N_DESTINATIONS=%d",
                      MAX_AGENTS,
                      MAX_NEIGHBORS,
                      MAX_DIMS,
                      N_DESTINATIONS);

   std::srand(opts.seed);
   mass::logger::info("seed used for simulation: %d", opts.seed);

   int dims = 2;
   int simSpace[] = {opts.size, opts.size};
   int numCells = opts.size * opts.size;

   int spawnPtNum = 4;
   int totalMacro = opts.init_macro_num + spawnPtNum;

   // initialize MASS
   mass::Mass::init();

   // create cell places to represent our simulation space.
   mass::Places* environmentPlaces = mass::Mass::createPlaces<EnvironmentPlace>(
       0,                                   // handle
       dims,                                // dimensions
       simSpace,                            // size of sim space
       mass::Place::MemoryOrder::ROW_MAJOR  // row-major place array
   );

   // The size of the simulation
   environmentPlaces->setAttribute<int>(EnvironmentAttributes::SIZE, 1, opts.size);
   // The maximum valid chemokine level.
   environmentPlaces->setAttribute<int>(EnvironmentAttributes::MAX_CHEMOKINE, 1, 2);
   // Day when tcells can enter blood vessels
   environmentPlaces->setAttribute<int>(EnvironmentAttributes::TCELL_ENTRANCE, 1, 10);
   environmentPlaces->setAttribute<bool>(EnvironmentAttributes::BACTERIA, 1, false);
   environmentPlaces->setAttribute<bool>(EnvironmentAttributes::BLOOD_VESSEL, 1, false);
   environmentPlaces->setAttribute<int>(EnvironmentAttributes::CHEMOKINE, 1, 0);
   environmentPlaces->setAttribute<bool>(EnvironmentAttributes::MACROPHAGE, 1, false);
   environmentPlaces->setAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_MACRO, 1, false);
   environmentPlaces->setAttribute<int>(EnvironmentAttributes::MACROPHAGE_STATE, 1, -1);
   environmentPlaces->setAttribute<bool>(EnvironmentAttributes::TCELL, 1, false);
   environmentPlaces->setAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_TCELL, 1, false);
   environmentPlaces->setAttribute<int>(EnvironmentAttributes::RAND_STATE, 1, 0);
   environmentPlaces->finalizeAttributes();

   environmentPlaces->callAll(EnvironmentFunctions::INITIALIZE_ENVIRONMENT, &opts.size);

   mass::logger::debug("Created environmentPlaces.");

   int* macroSpawn = new int[totalMacro];
   spawnInitialMacrophages(opts.size, macroSpawn, totalMacro);

   // create Macrophage Agents
   mass::Agents* macrophageAgents = mass::Mass::createAgents<Macrophage>(
       1,           // handle
       totalMacro,  // number of agents
       0,           // places handle
       numCells,    // max agents
       macroSpawn   // initial starting places
   );

   // The bacteria capacity that a macrophage can hold.
   macrophageAgents->setAttribute<int>(MacrophageAttributes::BACTERIA_CAPACITY, 1, 100);
   // The threshold of held bacteria which turns an infected macrophage to a chronically infected macrophage.
   macrophageAgents->setAttribute<int>(MacrophageAttributes::CHRONIC_INFECTION_LIMIT, 1, 75);
   // Number of bloodvessels for macrophage spawn points
   macrophageAgents->setAttribute<int>(MacrophageAttributes::SPAWN_POINT_NUM, 1, 4);
   macrophageAgents->setAttribute<int>(MacrophageAttributes::STATE, 1, State::RESTING);
   macrophageAgents->setAttribute<int>(MacrophageAttributes::IS_SPAWNER, 1);
   macrophageAgents->setAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1, 0);
   macrophageAgents->setAttribute<int>(MacrophageAttributes::INFECTED_TIME, 1);
   macrophageAgents->finalizeAttributes();

   macrophageAgents->callAll(MacrophageFunctions::INITIALIZE_MACRO);
   mass::logger::debug("Created macrophage agents.");

   int* tcellSpawn = new int[4];  // Only need to initialize spawners
   spawnInitialTCells(opts.size, tcellSpawn);
   for (int k = 0; k < 4; k++) {
      mass::logger::debug("tCellSpawn = %d.", tcellSpawn[k]); // TEST
   }

   // create TCell Agents
   mass::Agents* tcellAgents = mass::Mass::createAgents<TCell>(
       2,              // handle
       4,              // number of agents // TEST changed from 4
       0,              // places handle
       numCells,        // max agents
       tcellSpawn  // initial starting places
   );

   tcellAgents->setAttribute<bool>(TCellAttributes::TCELL_IS_SPAWNER, 1, false);
   tcellAgents->finalizeAttributes();

   tcellAgents->callAll(TCellFunctions::INITIALIZE_TCELL);
   mass::logger::debug("Created Tcell agents.");

   // Generate random values for each cell.
   int* randVals = generateRandVals(numCells);

   environmentPlaces->callAll(EnvironmentFunctions::INIT_RAND, randVals, sizeof(int) * numCells);
   delete[] randVals;
   mass::logger::debug("Initialized random values.");

   // Create neighborhood for each place
   std::vector<int*> neighbors;
   neighbors.push_back(new int[2]{0, 1});    // North
   neighbors.push_back(new int[2]{1, 1});    // North-East
   neighbors.push_back(new int[2]{1, 0});    // East
   neighbors.push_back(new int[2]{1, -1});   // South-East
   neighbors.push_back(new int[2]{0, -1});   // South
   neighbors.push_back(new int[2]{-1, -1});  // South-West
   neighbors.push_back(new int[2]{-1, 0});   // West
   neighbors.push_back(new int[2]{-1, 1});   // North-West

   environmentPlaces->exchangeAll(&neighbors, EnvironmentFunctions::FIX_NEIGHBORS, NULL, 0);
   mass::logger::debug("Exchanged neighbors.");

   // Output initial state
   if (interval != 0) {
      outputSimSpace(vizFile, environmentPlaces, opts.size);
   }

   // Start simulation loop
   for (int i = 0; i < opts.total_days; i++) {
      mass::logger::debug("\nStarting day %d.\n", i);

      environmentPlaces->callAll(EnvironmentFunctions::CHEMOKINE_DECAY);

      if (i > 0 && i % 10 == 0) {  // grows every 10 days

         environmentPlaces->callAll(EnvironmentFunctions::BACTERIA_GROWTH);
         mass::logger::debug("Bacteria growth at day %d.", i);
      }

      mass::logger::debug("\nEntering environmentalPlaces->callAll CELL_RECRUITMENT. i = %d, sizeof(i) = %d", i, sizeof(i));
      environmentPlaces->callAll(EnvironmentFunctions::CELL_RECRUITMENT, &i, sizeof(i));

      mass::logger::debug("\nEntering macrophageAgents->callAll MIGRATE_MACRO.");
      macrophageAgents->callAll(MacrophageFunctions::MIGRATE_MACRO);
      tcellAgents->callAll(TCellFunctions::MIGRATE_TCELL);

      macrophageAgents->manageAll();
      tcellAgents->manageAll();

      mass::logger::debug("\nEntering macrophageAgents->callAll UPDATE_MACRO_PLACE_STATE.");
      macrophageAgents->callAll(MacrophageFunctions::UPDATE_MACRO_PLACE_STATE);
      mass::logger::debug("\nEntering tcellAgents->callAll UPDATE_TCELL_PLACE_STATE.");
      tcellAgents->callAll(TCellFunctions::UPDATE_TCELL_PLACE_STATE);

      mass::logger::debug("\nEntering macrophageAgents->callAll UPDATE_STATE.");
      macrophageAgents->callAll(MacrophageFunctions::UPDATE_STATE);

      mass::logger::debug("\nEntering macrophageAgents->callAll SPAWN_MACRO.");
      macrophageAgents->callAll(MacrophageFunctions::SPAWN_MACRO);
      mass::logger::debug("\nEntering tcellAgents->callAll SPAWN_TCELL.");
      tcellAgents->callAll(TCellFunctions::SPAWN_TCELL);

      macrophageAgents->manageAll();
      tcellAgents->manageAll();

      mass::logger::debug("\nEntering macrophageAgents->callAll UPDATE_MACRO_PLACE_STATE.");
      macrophageAgents->callAll(MacrophageFunctions::UPDATE_MACRO_PLACE_STATE);
      mass::logger::debug("\nEntering tcellAgents->callAll UPDATE_TCELL_PLACE_STATE.");
      tcellAgents->callAll(TCellFunctions::UPDATE_TCELL_PLACE_STATE);

      // Output viz frame each 'interval' tick.
      if (interval != 0 && (i % interval == 0 || i == opts.total_days - 1)) {
         outputSimSpace(vizFile, environmentPlaces, opts.size);
      }
   }

   printf("\nTOTAL MACRO: %d\n", macrophageAgents->getNumAgents());

   // implement simulation...
   mass::logger::info("simulation complete, shutting down...");

   mass::Mass::finish();
}

ConfigOpts parseSimConfig(po::variables_map vm) {
   ConfigOpts opts = ConfigOpts{
       vm["seed"].as<int>(),
       vm["size"].as<int>(),
       vm["total_days"].as<int>(),
       vm["init_macro_num"].as<int>(),
   };

   // If seed is unset, set to current time in milli-seconds since
   // epoch
   if (opts.seed == -1) {
      std::time_t _time = std::time(NULL);
      opts.seed = _time;
   }

   mass::logger::debug(
       "Simulation Config: {seed=%d, size=%d, total_days=%d, "
       "init_macro_num=%d}",
       opts.seed,
       opts.size,
       opts.total_days,
       opts.init_macro_num);

   return opts;
}

void outputSimSpace(simviz::RGBFile& vizFile, mass::Places* places, int size) {
   unsigned char* spaceColor = new unsigned char[3]{255, 255, 255};                   // white
   unsigned char* bacteria = new unsigned char[3]{0, 0, 128};                         // black
   unsigned char* macrophageResting = new unsigned char[3]{0, 255, 0};                // green
   unsigned char* macrophageInfected = new unsigned char[3]{255, 255, 0};             // yellow
   unsigned char* macrophageActivated = new unsigned char[3]{0, 255, 255};            // light blue
   unsigned char* macrophageChronicallyInfected = new unsigned char[3]{128, 0, 128};  // purple
   unsigned char* tCell = new unsigned char[3]{0, 0, 255};                            // blue
   unsigned char* chemokineLevelOne = new unsigned char[3]{255, 140, 0};              // orange
   unsigned char* chemokineLevelTwo = new unsigned char[3]{255, 0, 0};                // red

   int indices[2];
   for (int row = 0; row < size * 2; row++) {
      indices[0] = row / 2;
      for (int col = 0; col < size * 2; col++) {
         indices[1] = col / 2;
         int rmi = places->getRowMajorIdx(indices);
         if (rmi != (indices[0] % size) * size + indices[1]) {
            mass::logger::error("Row Major Index is incorrect: [%d][%d] != %d",
                                row, col, rmi);

            continue;
         }

         // Download attributes needed for SimSpace output from device
         bool* bacteriaAttribute = places->downloadAttributes<bool>(EnvironmentAttributes::BACTERIA, 1);
         bool* macrophageAttribute = places->downloadAttributes<bool>(EnvironmentAttributes::MACROPHAGE, 1);
         int* macrophageStateAttribute = places->downloadAttributes<int>(EnvironmentAttributes::MACROPHAGE_STATE, 1);
         bool* tcellAttribute = places->downloadAttributes<bool>(EnvironmentAttributes::TCELL, 1);
         int* chemokineAttribute = places->downloadAttributes<int>(EnvironmentAttributes::CHEMOKINE, 1);

         unsigned char* color = spaceColor;

         if (row % 2 == 0) {
            if (col % 2 == 0) {  // top left
               if (bacteriaAttribute[rmi]) {
                  color = bacteria;
               }
            } else {  // top right
               if (macrophageAttribute[rmi]) {
                  switch (macrophageStateAttribute[rmi]) {
                     case State::RESTING:
                        color = macrophageResting;
                        break;
                     case State::INFECTED:
                        color = macrophageInfected;
                        break;
                     case State::ACTIVATED:
                        color = macrophageActivated;
                        break;
                     case State::CHRONICALLY_INFECTED:
                        color = macrophageChronicallyInfected;
                        break;
                     default:
                        break;
                  }
               }
            }
         } else {
            if (col % 2 == 0) {  // bottom left
               if (tcellAttribute[rmi]) {
                  color = tCell;
               }
            } else {  // bottom right
               if (chemokineAttribute[rmi] == 1) {
                  color = chemokineLevelOne;
               } else if (chemokineAttribute[rmi] == 2) {
                  color = chemokineLevelTwo;
               }
            }
         }

         vizFile.write((char*)color, simviz::NumRGBBytes);
         delete[] bacteriaAttribute;
         delete[] macrophageAttribute;
         delete[] macrophageStateAttribute;
         delete[] tcellAttribute;
         delete[] chemokineAttribute;
      }
   }
}

void spawnInitialMacrophages(int size, int* macroSpawn, int totalMacro) {
   int quadrant = size / 4;

   // Set spawner locations on centre of each quadrant
   macroSpawn[0] = quadrant - 1 + size * (quadrant - 1);        // Top Left
   macroSpawn[1] = size - quadrant + size * (quadrant - 1);     // Top Right
   macroSpawn[2] = quadrant - 1 + size * (size - quadrant);     // Bottom Left
   macroSpawn[3] = size - quadrant + size * (size - quadrant);  // Bottom Right

   std::vector<int> shufflePlaces;
   for (int i = 0; i < size * size; i++) {
      shufflePlaces.push_back(i);
   }

   std::random_shuffle(shufflePlaces.begin(), shufflePlaces.end());

   std::vector<int> retVec(&shufflePlaces[0], &shufflePlaces[totalMacro]);

   // copy to static array macroSpawn
   for (int i = 4; i < totalMacro; i++) {
      macroSpawn[i] = retVec[i];
   }
}

void spawnInitialTCells(int size, int* tcellSpawn) {
   int quadrant = size / 4;

   // Set spawner locations on centre of each quadrant
   tcellSpawn[0] = quadrant - 1 + size * (quadrant - 1);        // Top Left
   tcellSpawn[1] = size - quadrant + size * (quadrant - 1);     // Top Right
   tcellSpawn[2] = quadrant - 1 + size * (size - quadrant);     // Bottom Left
   tcellSpawn[3] = size - quadrant + size * (size - quadrant);  // Bottom Right
}

int* generateRandVals(int n) {
   int* randVals = new int[n];
   for (int i = 0; i < n; i++) {
      randVals[i] = rand();
   }

   return randVals;
}
}  // namespace tuberculosis