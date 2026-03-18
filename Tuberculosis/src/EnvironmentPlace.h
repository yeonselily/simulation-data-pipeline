#ifndef ENVIRONMENT_PLACE_H
#define ENVIRONMENT_PLACE_H

#include <mass/Place.h>

#include "Macrophage.h"
#include "TCell.h"

class Macrophage;
class TCell;

enum EnvironmentFunctions {
   INITIALIZE_ENVIRONMENT,
   INIT_RAND,
   FIX_NEIGHBORS,
   CHEMOKINE_DECAY,
   BACTERIA_GROWTH,
   CELL_RECRUITMENT,
   UPDATE_RANDOM_STATE,

   // Debug functions
   PRINT_STATE,
};

enum EnvironmentAttributes {
   SIZE,
   MAX_CHEMOKINE,
   TCELL_ENTRANCE,
   BACTERIA,
   BLOOD_VESSEL,
   CHEMOKINE,
   MACROPHAGE,
   SHOULD_SPAWN_MACRO,
   MACROPHAGE_STATE,
   TCELL,
   SHOULD_SPAWN_TCELL,
   RAND_STATE
};

// An EnvironmentPlace is a cell in the Tuberculosis simulation space.
class EnvironmentPlace : public mass::Place {
   public:
      MASS_FUNCTION EnvironmentPlace(int index) : Place(index) {};
      MASS_FUNCTION ~EnvironmentPlace() {};

      // Calls the method with the given arguments specified by the given function ID.
      __device__ virtual void callMethod(int functionId, void* arg = NULL);

      // Returns whether the bacterium exists.
      __device__ bool getBacteria();

      // Sets the existence of bacterium.
      __device__ void setBacteria(bool bacteria);

      // Returns the chemokine level.
      __device__ int getChemokine();

      // Sets the chemokine level.
      __device__ void setChemokine(int chemokine);

      // Returns whether the current cell has an agent specified by the given bool.
      __device__ bool isGoodForMigration(bool isMacrophage);

      // Returns whether there is a macrophage occupying the EnvironmentPlace.
      __device__ bool getMacrophage();

      // Sets the occupancy of macrophage at the EnvironmentPlace.
      __device__ void setMacrophage(bool macrophage);

      // Sets the macrophage state.
      __device__ void setMacrophageState(int state);

      // Returns the macrophage state.
      __device__ int getMacrophageState();

      // Returns whether there is a tcell occupying the EnvironmentPlace.
      __device__ bool getTCell();

      // Sets the occupancy of tcell at the EnvironmentPlace.
      __device__ void setTCell(bool tcell);

      // Updates the surrounding EnvironmentPlaces when the occupying Macrophage bursts.
      __device__ void burst();

      // Returns the relative index of the EnvironmentPlace with the highest chemokine
      // levels.
      __device__ int getHighestChemokine();

      /*    Getters    */
      __device__ bool getShouldSpawnMacro();
      __device__ bool getShouldSpawnTCell();

      /*    Setters    */
      __device__ void stopSpawningMacro();
      __device__ void stopSpawningTCell();

   private:

      // Initializes an EnvironmentPlace using the given simulation space index and
      // simulation size.
      __device__ void initialize();

      // Pass in generated random values from Host to Device
      __device__ void initRand(int randVal);

      // Assigns NULL to edge neighbors so agents can't move through "walls"
      __device__ void fixNeighbors();

      // Updates the chemokine level to decay with each simulation step
      __device__ void chemokineDecay();

      // Updates the growth of bacterium in the simulation space.
      __device__ void bacteriaGrowth();

      // Reserves the place with a 50% chance to spawn the cells
      __device__ void cellRecruitment(int day);

      // Updates random state
      __device__ void updateRandomState();
};

#endif
