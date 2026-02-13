#ifndef METAL_H
#define METAL_H

#include "mass/Place.h"

class Metal: public mass::Place {
public:

    enum FUNCTION{
        APPLY_HEAT,
        EULER_METHOD,
        SYNC_BORDERS
    };

    enum ATTRIBUTE{
        TEMPERATURE,
        PHASE,
        R
    };

    MASS_FUNCTION Metal(int index) : Place(index) {}
    MASS_FUNCTION ~Metal() {}

    __device__ virtual void callMethod(int functionId, void *arg = NULL);

private:
    __device__ void applyHeat();
    __device__ void syncBorders();
    __device__ void eulerMethod();

    __device__ void setBorders(int size, int p, int next_p);
	__device__ inline bool isBorderCell(int size);
};

#endif