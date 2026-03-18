#ifndef MACROPHAGE_H
#define MACROPHAGE_H

#include <mass/Agents.h>

#include "EnvironmentPlace.h"
#include "mass/Logger.h"

enum MacrophageFunctions {
   INITIALIZE_MACRO,
   MIGRATE_MACRO,
   UPDATE_STATE,
   SPAWN_MACRO,
   UPDATE_MACRO_PLACE_STATE,
};

enum MacrophageAttributes {
   BACTERIA_CAPACITY,
   CHRONIC_INFECTION_LIMIT,
   SPAWN_POINT_NUM,
   STATE,
   IS_SPAWNER,
   INTERNAL_BACTERIA,
   INFECTED_TIME
};

enum State {
   RESTING,
   INFECTED,
   ACTIVATED,
   CHRONICALLY_INFECTED
};
// The Macrophage is an agent in the Tuberculosis simulation that detects foreign
// bacteria in the immune system. Macrophages can be various states depending on
// the history of interactions in the simulation space.
class Macrophage : public mass::Agent {
  public:
   MASS_FUNCTION Macrophage(int index) : Agent(index) {};
   MASS_FUNCTION ~Macrophage() {};

   // Calls the method with the given arguments specified by the given function ID.
   __device__ virtual void callMethod(int functionId, void* arg = NULL);

  private:
   // Initializes start state
   __device__ void initialize();

   // Migrates the current macrophage to another EnvironmentPlace if possible.
   __device__ void migrate();

   // Applies the rules for a resting macrophage.
   __device__ void restingRules();

   // Applies the rules for a infected macrophage.
   __device__ void infectedRules();

   // Applies the rules for an activated macrophage.
   __device__ void activatedRules();

   // Applies the rules for a chronically infected macrophage.
   __device__ void chronicallyInfectedRules();

   // Destroys the infected macrophage and spreads chemokine to the surrounding
   // EnvironmentPlaces.
   __device__ void burst();

   // Updates the state of the macrophage based on its' current state.
   __device__ void updateState();

   // Invisible macrophage spawner cells spawn new macrophages if needed
   __device__ void spawnMacro();

   // Updates the state of the macrophage's current place to the
   // macrophage's current state.
   __device__ void updatePlaceState();
};

#endif
