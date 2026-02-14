#include <iostream>
#include <sstream>
#include <iomanip>
#include <vector>
#include <stdlib.h>

#include "Heat2D.h"
#include "Metal.h"
#include "mass/Mass.h"
#include "mass/Logger.h"
#include "mass/CudaEventTimer.h"
#include "Timer.h"

using namespace std;
using namespace mass;
using namespace logger;

#define USE_TIMER 1

static const double a = 1.0;  // heat speed
static const double dt = 1.0; // time quantum
static const double dd = 2.0; // change in system

Heat2D::Heat2D() {}
Heat2D::~Heat2D() {}

// getRGB retrieves the RGB color associated with the provided temp.
// It uses 19.0 as the point temp as that is what appears to be used
// in the rest of the implementation, and is not configurable. The color
// code is mapped to a unit circle with the +x representing the red value,
// -x representing the blue value, and +y representing green. x is known
// and we use the pythagorean theorem to find y.
unsigned char *getRGB(double temp)
{
	double pointTemp = 19.0;

	// lshift used to center temp on unit circle
	double lshift = pointTemp / 2;
	double x = temp - lshift;
	double x_sqrd = x * x;

	// calculate y
	double y = std::sqrt(1 - x_sqrd);

	// calculate and return RGB values
	unsigned char g = y * 255;
	unsigned char r = 0;
	unsigned char b = 0;
	if (x < 0)
	{
		b = std::abs(255 * x);
	}
	else if (x > 0)
	{
		r = 255 * x;
	}

	return new unsigned char[3]{r, g, b};
}

void Heat2D::displayResults(simviz::RGBFile &vizFile, mass::Places *places, int time, int *placesSize)
{
	mass::logger::debug("Entering Heat2d::displayResults");
	std::ostringstream ss;

	// set precision for temperature values
	ss << std::fixed << std::setprecision(3); 

	ss << "time = " << time << "\n";
	// mass::Place ** retVals = places->getElements(); //refreshes places here
	double *retVals = places->downloadAttributes<double>(Metal::ATTRIBUTE::TEMPERATURE, 2);
	int *phase = places->downloadAttributes<int>(Metal::ATTRIBUTE::PHASE, 1);
	int indices[2];
	for (int row = 0; row < placesSize[0]; row++)
	{
		indices[0] = row;
		for (int col = 0; col < placesSize[1]; col++)
		{
			indices[1] = col;
			int rmi = places->getRowMajorIdx(indices);
			if (rmi != (row % placesSize[0]) * placesSize[0] + col)
			{
				mass::logger::error("Row Major Index is incorrect: [%d][%d] != %d",
									row, col, rmi);
			}

			// double temp = ((Metal*) retVals[rmi])->getTemp();
			double temp = retVals[(rmi * 2 + phase[rmi])];
			ss << (temp / 2) << " ";

			vizFile.write((char *)getRGB(temp), simviz::NumRGBBytes);
		}

		ss << "\n";
	}
	ss << "\n";
	mass::logger::debug(ss.str());
	free(retVals);
	free(phase);
}

void Heat2D::display(mass::Places *places, int time, int *placesSize)
{
	mass::logger::debug("Entering Heat2d::displayResults");
	std::ostringstream ss;
	ss << std::fixed << std::setprecision(3);

	ss << "time = " << time << "\n";
	double *retVals = places->downloadAttributes<double>(Metal::ATTRIBUTE::TEMPERATURE, 2); // refreshes places here
	int *phase = places->downloadAttributes<int>(Metal::ATTRIBUTE::PHASE, 1);
	int indices[2];
	for (int row = 0; row < placesSize[0]; row++)
	{
		indices[0] = row;
		for (int col = 0; col < placesSize[1]; col++)
		{
			indices[1] = col;
			int rmi = places->getRowMajorIdx(indices);
			if (rmi != (row % placesSize[0]) * placesSize[0] + col)
			{
				mass::logger::error("Row Major Index is incorrect: [%d][%d] != %d",
									row, col, rmi);
			}

			// double temp = ((Metal*) retVals[rmi])->getTemp();
			double temp = retVals[(rmi * 2 + phase[rmi])];
			ss << (temp / 2) << " ";
		}

		ss << "\n";
	}
	ss << "\n";
	mass::logger::debug(ss.str());
	free(retVals);
	free(phase);
}

void Heat2D::runMassSim(int size, int max_time, int heat_time, int interval, simviz::RGBFile &vizFile)
{
	logger::debug("Starting MASS CUDA simulation\n");

	int nDims = 2;
	int placesSize[] = {size, size};

	// Start CPU clock timer
	Timer timer;
	timer.start();

#ifdef USE_TIMER
	// Start CUDA Event timer for overall simulation
	std::unique_ptr<mass::CudaEventTimer> simulationTimer = std::unique_ptr<mass::CudaEventTimer>(new mass::CudaEventTimer());
	simulationTimer->startTimer();
#endif

	// Initalize MASS
	Mass::init();

#ifdef USE_TIMER
	// Start CUDA Event timer for initalization
	std::unique_ptr<mass::CudaEventTimer> initTimer = std::unique_ptr<mass::CudaEventTimer>(new mass::CudaEventTimer());
	initTimer->startTimer();
#endif
	// Initalize Places
	mass::Places *places = mass::Mass::createPlaces<Metal>(0, nDims, placesSize,
														   mass::Place::MemoryOrder::ROW_MAJOR);

	// Initialize neighbors
	std::vector<int *> neighbors;
	/*
	int north[2] = {0, 1};
	int east[2] = {1, 0};
	int south[2] = {0, -1};
	int west[2] = {-1, 0};
	*/

	int north[2] = {-1, 0};
	int east[2] = {0, 1};
	int south[2] = {1, 0};
	int west[2] = {0, -1};

	neighbors.push_back(north);
	neighbors.push_back(east);
	neighbors.push_back(south);
	neighbors.push_back(west);

	places->exchangeAll(&neighbors);

	// Setting attributes
	places->setAttribute<double>(Metal::TEMPERATURE, 2, 0.0);
	places->setAttribute<int>(Metal::PHASE, 1, 0);
	places->setAttribute<double>(Metal::R, 1, a * dt / (dd * dd));
	places->finalizeAttributes();

	
#ifdef USE_TIMER
	// Stop CUDA Event timer for initialization
	initTimer->stopTimer();
	long initCpuTime = timer.lap();
#endif

	// Calculate the avg step CUDA time
	float avgStepTime = 0.0;

	for (int time = 0; time < max_time; time++)
	{
#ifdef USE_TIMER
		// Start a CUDA Event timer for each step
		std::unique_ptr<mass::CudaEventTimer> stepTimer = std::unique_ptr<mass::CudaEventTimer>(new mass::CudaEventTimer());
		stepTimer->startTimer();
#endif
		// places->exchangeAll(&neighbors, Metal::SYNC_BORDERS, width, 1);
		// places->exchangeAll(&neighbors, Metal::SYNC_BORDERS);
		places->callAll(Metal::SYNC_BORDERS);

		if (time < heat_time)
		{
			// places->callAll(Metal::APPLY_HEAT, width, 1);
			places->callAll(Metal::APPLY_HEAT);
		}

		// display intermediate results
		if (interval != 0 && (time % interval == 0 || time == max_time - 1))
		{
			displayResults(vizFile, places, time, placesSize);
			// display(places, time, placesSize);
		}

		// places->exchangeAll(&neighbors, Metal::EULER_METHOD, width, 1);
		// places->exchangeAll(&neighbors, Metal::EULER_METHOD);
		places->callAll(Metal::EULER_METHOD);
		
		// printf("Step %d done.\n", time);
#ifdef USE_TIMER
		// Stop the CUDA Event timer for each step
		stepTimer->stopTimer();
		avgStepTime += stepTimer->getElapsedTime();
		// logger::info("Step %d time %d ms", time, stepTimer->getElapsedTime());
#endif
	}

#ifdef USE_TIMER
	// End of simulation, stop the CUDA Event timer for all timers
	simulationTimer->stopTimer();
	logger::info("CUDA total time %f ms", simulationTimer->getElapsedTime());
	logger::info("CUDA time for initialization %f ms", initTimer->getElapsedTime());
	logger::info("CPU time for initialization %ld ms", initCpuTime / 1000);
	logger::info("CUDA avg step time %f ms", avgStepTime / max_time);
#endif

	logger::info("MASS time %ld ms", timer.lap() / 1000);

	Mass::finish();
}