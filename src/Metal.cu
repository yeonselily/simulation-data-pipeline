#include "Metal.h"
#include "mass/settings.h"
#include <cmath>

using namespace std;
using namespace mass;

__device__ void Metal::callMethod(int functionId, void *argument)
{
    switch (functionId) {
	case APPLY_HEAT:
		applyHeat();
		break;
	case SYNC_BORDERS:
		syncBorders();
        break;
	case EULER_METHOD:
		eulerMethod();
		break;
	default:
		break;
	}
}

__device__ void Metal::applyHeat() {
	unsigned int totalPlaces = getNumPlaces();
	unsigned int size = ((unsigned int)sqrt((double)totalPlaces));

    int index = getIndex();
	double *heat = getAttribute<double>(index, ATTRIBUTE::TEMPERATURE, 2);
	int *p = getAttribute<int>(index, ATTRIBUTE::PHASE, 1);
	
	if(index >= size / 3 && index < size / 3 * 2) { 
		heat[*p] = 19.0; 
	}

    //printf("%d, Metal at index: %d, heat[0]: %f heat[1]: %f, phase: %d\n", *size, index, heat[0], heat[1], *p);
}

__device__ void Metal::eulerMethod() {
	unsigned int totalPlaces = getNumPlaces();
	unsigned int size = ((unsigned int)sqrt((double)totalPlaces));

	int index = getIndex();
	int *p = getAttribute<int>(index, ATTRIBUTE::PHASE, 1);
	int p2 = (*p + 1) % 2; // next phase
	
	if( !isBorderCell(size) ) { // forward euler
		int *neighbors = getAttribute<int>(index, PlacePreDefinedAttr::NEIGHBORS, MAX_NEIGHBORS);

		double *north = getAttribute<double>(neighbors[0], ATTRIBUTE::TEMPERATURE, 2);
		double *east = getAttribute<double>(neighbors[1], ATTRIBUTE::TEMPERATURE, 2);
		double *south = getAttribute<double>(neighbors[2], ATTRIBUTE::TEMPERATURE, 2);
		double *west = getAttribute<double>(neighbors[3], ATTRIBUTE::TEMPERATURE, 2);

		double *r = getAttribute<double>(index, ATTRIBUTE::R, 1);

		double *myTemp = getAttribute<double>(index, ATTRIBUTE::TEMPERATURE, 2);
		double curTemp = myTemp[*p];

		myTemp[p2] = curTemp + r[0] * (east[*p] - 2 * curTemp + west[*p]) 
			+ r[0] * (south[*p] - 2 * curTemp + north[*p]);

	}
	else { // copying to border
		//setBorders(*size, *p, p2);
	}
	// next phase
	p[0] = p2;
}

__device__ void Metal::setBorders(int size, int p, int next_p) {
	int index = getIndex();
	int idx;

	if (index < size) { // top border
		idx = 2; // south neighbor value
	} 
	if (index >= size * size - size) {  // bottom border
		idx = 0; // north neighbor value
	}
	if (index % size == 0) { // left border
		idx = 1;  // east neighbor value
	}
 	else if (index % size == size - 1) {  // right border
		idx = 3; // west neighbor value
	}

	int *neighbors = getAttribute<int>(index, PlacePreDefinedAttr::NEIGHBORS, MAX_NEIGHBORS);

	double *temp = getAttribute<double>(index, ATTRIBUTE::TEMPERATURE, 2);
	double *neighborTemp = getAttribute<double>(neighbors[idx], ATTRIBUTE::TEMPERATURE, 2);
	temp[next_p] = neighborTemp[p];
}

__device__ inline bool Metal::isBorderCell(int size) {
	int index = getIndex();
	return (index < size || index > size * size - size || index % size == 0
			|| index % size == size - 1);
}

__device__ void Metal::syncBorders() {
	unsigned int totalPlaces = getNumPlaces();
	unsigned int size = ((unsigned int)sqrt((double)totalPlaces));

	int index = getIndex();
	int idx;
	int *p = getAttribute<int>(index, ATTRIBUTE::PHASE, 1);

	if( isBorderCell(size) ) { // forward euler
		if (index < (size)) { // top border
			idx = 2; // south neighbor value
		} 
		else if (index >= (size) * (size) - (size)) {  // bottom border
			idx = 0; // north neighbor value
		}
		else if ((index % (size)) == 0) { // left border
			idx = 1;  // east neighbor value
		}
		else if (index % (size) == (size) - 1) {  // right border
			idx = 3; // west neighbor value
		}

		int *neighbors = getAttribute<int>(index, PlacePreDefinedAttr::NEIGHBORS, MAX_NEIGHBORS);
		double *temp = getAttribute<double>(index, ATTRIBUTE::TEMPERATURE, 2);
		double *neighborTemp = getAttribute<double>(neighbors[idx], ATTRIBUTE::TEMPERATURE, 2);

		temp[*p] = neighborTemp[*p];
	}
}