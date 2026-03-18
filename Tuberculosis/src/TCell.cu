#include "TCell.h"

__device__ void TCell::callMethod(int functionId, void* arg) {
   switch (functionId) {
      case TCellFunctions::INITIALIZE_TCELL:
         initialize();
         break;
      case TCellFunctions::MIGRATE_TCELL:
         migrate();
         break;
      case TCellFunctions::SPAWN_TCELL:
         spawnTCell();
         break;
      case TCellFunctions::UPDATE_TCELL_PLACE_STATE:
         updatePlaceState();
         break;
      default:
         break;
   }
}

__device__ void TCell::initialize() {
   *getAttribute<bool>(TCellAttributes::TCELL_IS_SPAWNER, 1) = true;
}

__device__ void TCell::migrate() {
   if (*getAttribute<bool>(TCellAttributes::TCELL_IS_SPAWNER, 1)) return;

   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();  // current place

   if (myPlace != NULL) {  // place exists
      int highestChemokineIdx = myPlace->getHighestChemokine();
      if (highestChemokineIdx != -1) {
         myPlace->setTCell(false);

         // Debug
         // printf("Agent: %d From: %d Migrating to: %d Direction:%d\n", getIndex(), myPlace->getIndex(), myPlace->state->neighbors[highestChemokineIdx]->getIndex(), highestChemokineIdx);
         Agent::migrate((myPlace->getNeighborsPtr())[highestChemokineIdx]);
      }
   }
}

__device__ void TCell::spawnTCell() {
   if (*getAttribute<bool>(TCellAttributes::TCELL_IS_SPAWNER, 1)) {
      EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
      bool shouldSpawn = myPlace->getShouldSpawnTCell();
      if (shouldSpawn) {
         spawn(1, myPlace);
         myPlace->stopSpawningTCell();
      }
   }
}

__device__ void TCell::updatePlaceState() {
   if (*getAttribute<bool>(TCellAttributes::TCELL_IS_SPAWNER, 1)) return;
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   myPlace->setTCell(true);
}