#ifndef TCELL_H
#define TCELL_H

#include <mass/Agents.h>

#include "EnvironmentPlace.h"
#include "mass/Logger.h"

enum TCellFunctions {
   INITIALIZE_TCELL,
   MIGRATE_TCELL,
   SPAWN_TCELL,
   UPDATE_TCELL_PLACE_STATE,
};

enum TCellAttributes {
   TCELL_IS_SPAWNER
};

// The T-Cell is an agent in Tuberculosis simulation that activates infected
// macrophages and kills chronically infected macrophages
class TCell : public mass::Agent {
   public:
      MASS_FUNCTION TCell(int index) : Agent(index) {};
      MASS_FUNCTION ~TCell() {};

      // Calls the method with the given arguments specified by the given function ID.
      __device__ virtual void callMethod(int functionId, void* arg = NULL);

   private:
      // Only called on spawners - initializes start state
      __device__ void initialize();

      // Migrates the current T-Cell to another EnvironmentPlace if possible.
      __device__ void migrate();

      // Invisible TCell spawner cells spawn new TCells if needed
      __device__ void spawnTCell();

      // Sets TCell of the TCell's current place to true
      __device__ void updatePlaceState();
};

#endif