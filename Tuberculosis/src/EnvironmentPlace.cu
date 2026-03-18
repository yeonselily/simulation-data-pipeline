#include "EnvironmentPlace.h"

using namespace std;
using namespace mass;

__device__ void EnvironmentPlace::callMethod(int functionId, void* arg) {
   switch (functionId) {
      case EnvironmentFunctions::INITIALIZE_ENVIRONMENT:
         initialize();
         break;
      case EnvironmentFunctions::INIT_RAND:
         initRand(((int*)arg)[getIndex()]);
         break;
      case EnvironmentFunctions::FIX_NEIGHBORS:
         fixNeighbors();
         break;
      case EnvironmentFunctions::CHEMOKINE_DECAY:
         chemokineDecay();
         break;
      case EnvironmentFunctions::BACTERIA_GROWTH:
         bacteriaGrowth();
         break;
      case EnvironmentFunctions::CELL_RECRUITMENT:
         cellRecruitment(*(int*)arg);
         break;
      case EnvironmentFunctions::UPDATE_RANDOM_STATE:
         updateRandomState();
         break;
      default:
         break;
   }
}

__device__ bool EnvironmentPlace::getBacteria() {
   return *getAttribute<bool>(EnvironmentAttributes::BACTERIA, 1);
}

__device__ void EnvironmentPlace::setBacteria(bool newBacteria) {
   if (*getAttribute<bool>(EnvironmentAttributes::BACTERIA, 1) != newBacteria) {
      *getAttribute<bool>(EnvironmentAttributes::BACTERIA, 1) = newBacteria;
   }
}

__device__ int EnvironmentPlace::getChemokine() {
   return *getAttribute<int>(EnvironmentAttributes::CHEMOKINE, 1);
}

__device__ void EnvironmentPlace::setChemokine(int newChemokine) {
   int chemokineLevel = newChemokine;
   if (chemokineLevel < 0) {
      chemokineLevel = 0;
   }
   else if (chemokineLevel > *getAttribute<int>(EnvironmentAttributes::MAX_CHEMOKINE, 1)) {
      chemokineLevel = *getAttribute<int>(EnvironmentAttributes::MAX_CHEMOKINE, 1);
   }
   if (*getAttribute<int>(EnvironmentAttributes::CHEMOKINE, 1) != chemokineLevel) {
      *getAttribute<int>(EnvironmentAttributes::CHEMOKINE, 1) = chemokineLevel;
   }
}

__device__ bool EnvironmentPlace::isGoodForMigration(bool isMacrophage) {
   return !getMacrophage();
}

__device__ bool EnvironmentPlace::getMacrophage() {
   return *getAttribute<bool>(EnvironmentAttributes::MACROPHAGE, 1);
}

__device__ void EnvironmentPlace::setMacrophage(bool newMacrophage) {
   if (*getAttribute<bool>(EnvironmentAttributes::MACROPHAGE, 1) != newMacrophage) {
      *getAttribute<bool>(EnvironmentAttributes::MACROPHAGE, 1) = newMacrophage;
   }
}

__device__ int EnvironmentPlace::getMacrophageState() {
   return *getAttribute<int>(EnvironmentAttributes::MACROPHAGE_STATE, 1);
}

__device__ void EnvironmentPlace::setMacrophageState(int state) {
   *getAttribute<int>(EnvironmentAttributes::MACROPHAGE_STATE, 1) = state;
}

__device__ bool EnvironmentPlace::getTCell() {
   return *getAttribute<bool>(EnvironmentAttributes::TCELL, 1);
}

__device__ void EnvironmentPlace::setTCell(bool newTCell) {
   if (*getAttribute<bool>(EnvironmentAttributes::TCELL, 1) != newTCell) {
      *getAttribute<bool>(EnvironmentAttributes::TCELL, 1) = newTCell;
   }
}

__device__ void EnvironmentPlace::burst() {
   setBacteria(true);
   for (int i = 0; i < MAX_NEIGHBORS; i++) {
      EnvironmentPlace* neighbor = (EnvironmentPlace*)(getNeighborsPtr()[i]);
      if (neighbor != NULL)
         neighbor->setBacteria(true);
   }
}

__device__ int EnvironmentPlace::getHighestChemokine() {
   int highestVal = 0;
   int count = 0;

   for (int i = 0; i < MAX_NEIGHBORS; i++) {
      EnvironmentPlace* neighbor = (EnvironmentPlace*)(getNeighborsPtr()[i]);
      if (neighbor != NULL) {
         int neighborChemokine = neighbor->getChemokine();
         if (neighborChemokine > highestVal) {
            highestVal = neighborChemokine;
            count = 0;
         }
         if (neighborChemokine == highestVal && !*getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_MACRO, 1)) {
            count++;
         }
      }
   }

   int highestValIndex = 0;
   updateRandomState();
   int randVal = *getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1);
   highestValIndex = randVal % count;
   if (highestValIndex < 0) {
      highestValIndex = -highestValIndex;
   }
   highestValIndex++;

   for (int i = 0; i < MAX_NEIGHBORS; i++) {
      EnvironmentPlace* neighbor = (EnvironmentPlace*)(getNeighborsPtr()[i]);
      if (neighbor != NULL) {
         if (neighbor->getChemokine() == highestVal && !*getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_MACRO, 1)) highestValIndex--;
         if (highestValIndex == 0) {
            return i;
         }
      }
   }
   return -1;
}

__device__ void EnvironmentPlace::initialize() {
   int index = getIndex();
   int size = *getAttribute<int>(EnvironmentAttributes::SIZE, 1);
   int j = index % size, i = index / size;
   int half = size / 2, quadrant = size / 4;
   if ((i == half - 1 || i == half) && (j == half - 1 || j == half)) {
      setBacteria(true);
   } else {
      setBacteria(false);
   }
   if ((i == quadrant - 1 || i == size - quadrant) && (j == quadrant - 1 || j == size - quadrant)) {
      *getAttribute<bool>(EnvironmentAttributes::BLOOD_VESSEL, 1) = true;
   }
   *getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1) = 0;
}

__device__ void EnvironmentPlace::initRand(int randVal) {
   *getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1) = randVal;
}

__device__ void EnvironmentPlace::fixNeighbors() {
   int index = getIndex();
   int size = *getAttribute<int>(EnvironmentAttributes::SIZE, 1);
   if (index < size) {
      (getNeighborsPtr()[0]) = (getNeighborsPtr()[1]) = (getNeighborsPtr()[7]) = nullptr;
   }
   if (index >= size * size - size) {
      (getNeighborsPtr()[3]) = (getNeighborsPtr()[4]) = (getNeighborsPtr()[5]) = nullptr;
   }
   if (index % size == 0) {
      (getNeighborsPtr()[5]) = (getNeighborsPtr()[6]) = (getNeighborsPtr()[7]) = nullptr;
   }
   if (index % size == size - 1) {
      (getNeighborsPtr()[1]) = (getNeighborsPtr()[2]) = (getNeighborsPtr()[3]) = nullptr;
   }
}

__device__ void EnvironmentPlace::chemokineDecay() {
   setChemokine(getChemokine() - 1);
   if (!getMacrophage()) return;
   int macrophageState = *getAttribute<int>(EnvironmentAttributes::MACROPHAGE_STATE, 1);
   if (macrophageState == State::RESTING || macrophageState == State::INFECTED || macrophageState == State::CHRONICALLY_INFECTED) {
      setChemokine(*getAttribute<int>(EnvironmentAttributes::MAX_CHEMOKINE, 1));
      for (int i = 0; i < MAX_NEIGHBORS; i++) {
         EnvironmentPlace* neighbor = (EnvironmentPlace*)(getNeighborsPtr()[i]);
         if (neighbor != NULL)
            neighbor->setChemokine(*getAttribute<int>(EnvironmentAttributes::MAX_CHEMOKINE, 1));
      }
   }
}

__device__ void EnvironmentPlace::bacteriaGrowth() {
   if (!getBacteria()) return;
   for (int i = 0; i < MAX_NEIGHBORS; i++) {
      EnvironmentPlace* neighbor = (EnvironmentPlace*)(getNeighborsPtr()[i]);
      if (neighbor != NULL)
         neighbor->setBacteria(true);
   }
}

__device__ void EnvironmentPlace::cellRecruitment(int day) {
   if (!*getAttribute<bool>(EnvironmentAttributes::BLOOD_VESSEL, 1)) return;

   if (!*getAttribute<bool>(EnvironmentAttributes::MACROPHAGE, 1)) {
      updateRandomState();
      if (*getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1) % 100 < 50) {
         *getAttribute<bool>(EnvironmentAttributes::MACROPHAGE, 1) = true;
         *getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_MACRO, 1) = true;
      }
   }

   if (day > *getAttribute<int>(EnvironmentAttributes::TCELL_ENTRANCE, 1) && !*getAttribute<bool>(EnvironmentAttributes::TCELL, 1)) {
      updateRandomState();
      if (*getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1) % 100 < 50) {
         *getAttribute<bool>(EnvironmentAttributes::TCELL, 1) = true;
         *getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_TCELL, 1) = true;
      }
   }
}

__device__ void EnvironmentPlace::updateRandomState() {
   *getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1) += (*getAttribute<int>(EnvironmentAttributes::RAND_STATE, 1) + 1) * (getIndex() + 42) * 1662169368;
}

__device__ bool EnvironmentPlace::getShouldSpawnMacro() { return *getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_MACRO, 1);}
__device__ bool EnvironmentPlace::getShouldSpawnTCell() { return *getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_TCELL, 1); }

__device__ void EnvironmentPlace::stopSpawningMacro() { *getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_MACRO, 1) = false; }
__device__ void EnvironmentPlace::stopSpawningTCell() { *getAttribute<bool>(EnvironmentAttributes::SHOULD_SPAWN_TCELL, 1) = false; }