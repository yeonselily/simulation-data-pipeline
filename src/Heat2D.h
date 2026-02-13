#ifndef HEAT2D_H_
#define HEAT2D_H_

#include "Metal.h"
#include "mass/Places.h"
#include <vector>
#include "simviz.h"
using namespace std;

class Heat2D {
public:
    Heat2D();
    virtual ~Heat2D();

    void displayResults(simviz::RGBFile& vizFile, mass::Places *places, int time, int *placesSize);
    void display(mass::Places *places, int time, int *placesSize);
    void runMassSim(int size, int max_time, int heat_time, int interval, simviz::RGBFile& vizFile);
    void testMassSim(int size, int max_time, int heat_time, int interval);
};

#endif