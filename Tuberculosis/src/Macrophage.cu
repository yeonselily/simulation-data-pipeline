#include "Macrophage.h"

__device__ void Macrophage::callMethod(int functionId, void* argument) {
   switch (functionId) {
      case MacrophageFunctions::INITIALIZE_MACRO:
         initialize();
         break;
      case MacrophageFunctions::MIGRATE_MACRO:
         migrate();
         break;
      case MacrophageFunctions::UPDATE_STATE:
         updateState();
         break;
      case MacrophageFunctions::SPAWN_MACRO:
         spawnMacro();
         break;
      case MacrophageFunctions::UPDATE_MACRO_PLACE_STATE:
         updatePlaceState();
         break;
      default:
         break;
   }
}

__device__ void Macrophage::initialize() {
   // set up agent variables
   *getAttribute<int>(MacrophageAttributes::IS_SPAWNER, 1) = getIndex() < *getAttribute<int>(MacrophageAttributes::SPAWN_POINT_NUM, 1);
   updatePlaceState();
}

__device__ void Macrophage::migrate() {
   if (*getAttribute<int>(MacrophageAttributes::IS_SPAWNER, 1)) return;

   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();  // current place

   if (myPlace != NULL) {  // place exists
      int highestChemokineIdx = myPlace->getHighestChemokine();
      if (highestChemokineIdx != -1) {
         myPlace->setMacrophage(false);

         // Debug
         // printf("Agent: %d From: %d Migrating to: %d Direction:%d\n", getIndex(), myPlace->getIndex(), myPlace->state->neighbors[highestChemokineIdx]->getIndex(), highestChemokineIdx);
         Agent::migrate((myPlace->getNeighborsPtr())[highestChemokineIdx]);
      }
   }
}

__device__ void Macrophage::updateState() {
   if (*getAttribute<int>(MacrophageAttributes::IS_SPAWNER, 1)) return;

   switch (*getAttribute<int>(MacrophageAttributes::STATE, 1)) {
      case RESTING:
         restingRules();
         break;
      case INFECTED:
         infectedRules();
         break;
      case ACTIVATED:
         activatedRules();
         break;
      case CHRONICALLY_INFECTED:
         chronicallyInfectedRules();
         break;
      default:
         break;
   }
}

__device__ void Macrophage::restingRules() {
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   if (myPlace == NULL || !myPlace->getBacteria()) return;
   myPlace->setBacteria(false);
   *getAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1) = 1;
   *getAttribute<int>(MacrophageAttributes::STATE, 1) = INFECTED;
   *getAttribute<int>(MacrophageAttributes::INFECTED_TIME, 1) = 0;
}

__device__ void Macrophage::infectedRules() {
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   if (myPlace == NULL) return;
   (*getAttribute<int>(MacrophageAttributes::INFECTED_TIME, 1))++;
   *getAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1) = 2 * (*getAttribute<int>(MacrophageAttributes::INFECTED_TIME, 1)) + 1;
   if (*getAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1) > *getAttribute<int>(MacrophageAttributes::CHRONIC_INFECTION_LIMIT, 1)) {
      *getAttribute<int>(MacrophageAttributes::STATE, 1) = CHRONICALLY_INFECTED;
   } else if (myPlace != NULL && myPlace->getTCell()) {
      *getAttribute<int>(MacrophageAttributes::STATE, 1) = ACTIVATED;
      *getAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1) = *getAttribute<int>(MacrophageAttributes::INFECTED_TIME, 1) = 0;
   }
}

__device__ void Macrophage::activatedRules() {
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   if (myPlace == NULL || !myPlace->getBacteria()) return;
   myPlace->setBacteria(false);
}

__device__ void Macrophage::chronicallyInfectedRules() {
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   if (myPlace == NULL) return;
   *getAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1) += 2;
   if ((myPlace != NULL && myPlace->getTCell()) || *getAttribute<int>(MacrophageAttributes::INTERNAL_BACTERIA, 1) >= *getAttribute<int>(MacrophageAttributes::BACTERIA_CAPACITY, 1)) {
      burst();
   }
}

__device__ void Macrophage::burst() {
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   if (myPlace == NULL) return;
   myPlace->burst();
   myPlace->setMacrophage(false);
   terminate();
}

__device__ void Macrophage::spawnMacro() {
   if (*getAttribute<int>(MacrophageAttributes::IS_SPAWNER, 1)) {
      EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
      bool shouldSpawn = myPlace->getShouldSpawnMacro();
      if (shouldSpawn) {
         spawn(1, myPlace);
         myPlace->stopSpawningMacro();
      }
   }
}

__device__ void Macrophage::updatePlaceState() {
   if (*getAttribute<int>(MacrophageAttributes::IS_SPAWNER, 1)) {
      return;
   }
   EnvironmentPlace* myPlace = (EnvironmentPlace*)getPlace();
   // printf("Agent %d is on place %llu\n", getIndex(), getPlaceIndex()); // TEST
   myPlace->setMacrophage(true);
   myPlace->setMacrophageState(*getAttribute<int>(MacrophageAttributes::STATE, 1));
}